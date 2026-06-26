import datetime
import uuid

from django.db import transaction
from django.utils import timezone
from django.utils.dateparse import parse_date
from rest_framework.decorators import api_view, authentication_classes

from CSAA.auth.authentication import AdminTokenAuthtication
from CSAA.course_conflicts import student_slot_conflict_on_date
from CSAA.handler import APIResponse
from CSAA.models import Lesson, Order, PermanentCourseChange
from CSAA.views.admin.daily_adjustment import _occupied_count


DAY_INDEX = {'Mon': 0, 'Tue': 1, 'Wed': 2, 'Thu': 3, 'Fri': 4, 'Sat': 5, 'Sun': 6}


def _at_start(date_value):
    return datetime.datetime.combine(date_value, datetime.time.min)


def _at_end(date_value):
    return datetime.datetime.combine(date_value, datetime.time.max)


def _first_class_date(thing, effective_date):
    day_index = DAY_INDEX.get(thing.day)
    if day_index is None:
        return None
    return effective_date + datetime.timedelta(
        days=(day_index - effective_date.weekday()) % 7,
    )


def _source_order(student_id, source_lesson_id, effective_date):
    return Order.objects.select_related(
        'child',
        'user',
        'thing',
        'term',
    ).filter(
        child_id=student_id,
        thing__thing_lesson__id=source_lesson_id,
        status=6,
        expect_time__date__lte=effective_date,
        return_time__date__gte=effective_date,
    ).first()


def _serialize(record):
    return {
        'id': record.id,
        'student_id': record.student_id,
        'student_name': record.student.name,
        'effective_date': record.effective_date.strftime('%Y-%m-%d'),
        'source_lesson_id': record.source_lesson_id,
        'source_class': record.source_lesson.thing.title,
        'target_lesson_id': record.target_lesson_id,
        'target_class': record.target_lesson.thing.title,
        'target_day': record.target_lesson.thing.day,
        'target_time': record.target_lesson.thing.time.time,
        'target_room': record.target_lesson.thing.tag.title,
        'reason': record.reason,
        'status': record.status,
    }


@api_view(['GET'])
@authentication_classes([AdminTokenAuthtication])
def options(request):
    student_id = request.GET.get('student_id')
    source_lesson_id = request.GET.get('source_lesson_id')
    effective_date = parse_date(request.GET.get('effective_date', ''))
    if not effective_date:
        return APIResponse(code=1, msg='A valid effective date is required')

    source_order = _source_order(student_id, source_lesson_id, effective_date)
    if not source_order:
        return APIResponse(code=1, msg='No active source enrollment exists on the effective date')

    lessons = Lesson.objects.filter(
        thing__status='0',
    ).exclude(id=source_lesson_id).select_related(
        'thing',
        'thing__time',
        'thing__tag',
    ).order_by('thing__day', 'thing__time__time', 'thing__tag__title')

    data = []
    for lesson in lessons:
        first_date = _first_class_date(lesson.thing, effective_date)
        if not first_date or first_date > source_order.return_time.date():
            continue
        data.append({
            'lesson_id': lesson.id,
            'class_name': lesson.thing.title,
            'day': lesson.thing.day,
            'time': lesson.thing.time.time if lesson.thing.time else None,
            'room': lesson.thing.tag.title if lesson.thing.tag else None,
            'capacity': lesson.thing.tag.seat if lesson.thing.tag else 0,
            'first_class_date': first_date.strftime('%Y-%m-%d'),
        })
    return APIResponse(code=0, msg='Query successful', data=data)


@api_view(['GET'])
@authentication_classes([AdminTokenAuthtication])
def list_api(request):
    records = PermanentCourseChange.objects.filter(
        status='active',
    ).select_related(
        'student',
        'source_lesson__thing',
        'target_lesson__thing__time',
        'target_lesson__thing__tag',
    ).order_by('-created_time')
    return APIResponse(code=0, msg='Query successful', data=[_serialize(record) for record in records])


@api_view(['POST'])
@authentication_classes([AdminTokenAuthtication])
@transaction.atomic
def create(request):
    effective_date = parse_date(str(request.data.get('effective_date', '')))
    student_id = request.data.get('student_id')
    source_lesson_id = request.data.get('source_lesson_id')
    target_lesson_id = request.data.get('target_lesson_id')
    reason = str(request.data.get('reason', '')).strip()
    if not effective_date:
        return APIResponse(code=1, msg='A valid effective date is required')

    source_order = _source_order(student_id, source_lesson_id, effective_date)
    if not source_order:
        return APIResponse(code=1, msg='No active source enrollment exists on the effective date')
    if PermanentCourseChange.objects.filter(
        source_order=source_order,
        status='active',
    ).exists():
        return APIResponse(code=1, msg='This enrollment already has an active permanent change')

    try:
        source_lesson = Lesson.objects.select_related('thing').get(id=source_lesson_id)
        target_lesson = Lesson.objects.select_related(
            'thing',
            'thing__time',
            'thing__tag',
        ).get(id=target_lesson_id, thing__status='0')
    except Lesson.DoesNotExist:
        return APIResponse(code=1, msg='Source or target class does not exist')
    if source_lesson.id == target_lesson.id:
        return APIResponse(code=1, msg='Source and target classes are the same')

    first_target_date = _first_class_date(target_lesson.thing, effective_date)
    if not first_target_date or first_target_date > source_order.return_time.date():
        return APIResponse(code=1, msg='The target class has no remaining lesson in this enrollment period')
    capacity = int(target_lesson.thing.tag.seat or 0)
    if capacity and _occupied_count(target_lesson, first_target_date) >= capacity:
        return APIResponse(code=1, msg=f'{target_lesson.thing.tag.title} is full')
    conflict = student_slot_conflict_on_date(
        source_order.child,
        target_lesson.thing,
        first_target_date,
        exclude_order_id=source_order.id,
    )
    if conflict:
        return APIResponse(code=1, msg=conflict)

    original_return_time = source_order.return_time
    transferred_count = source_order.num
    source_order.return_time = _at_end(effective_date - datetime.timedelta(days=1))
    source_order.num = 0
    source_order.save(update_fields=['return_time', 'num'])

    target_order = Order.objects.create(
        order_number='P' + uuid.uuid4().hex[:12].upper(),
        user=source_order.user,
        thing=target_lesson.thing,
        count=source_order.count,
        num=transferred_count,
        child=source_order.child,
        expect_time=_at_start(effective_date),
        return_time=original_return_time,
        term=source_order.term,
        amount=source_order.amount,
        status=6,
        pay_time=source_order.pay_time,
        receiver_name=source_order.receiver_name,
        receiver_address=source_order.receiver_address,
        receiver_phone=source_order.receiver_phone,
        remark='Permanent course change',
    )
    source_lesson.students.remove(source_order.child)
    target_lesson.students.add(source_order.child)

    record = PermanentCourseChange.objects.create(
        student=source_order.child,
        effective_date=effective_date,
        source_order=source_order,
        target_order=target_order,
        source_lesson=source_lesson,
        target_lesson=target_lesson,
        original_source_return_time=original_return_time,
        transferred_lesson_count=transferred_count,
        reason=reason,
        created_by=request.user,
    )
    return APIResponse(code=0, msg='Permanent course change saved', data=_serialize(record))


@api_view(['POST'])
@authentication_classes([AdminTokenAuthtication])
@transaction.atomic
def revert(request):
    try:
        record = PermanentCourseChange.objects.select_for_update().select_related(
            'source_order',
            'target_order',
            'student',
            'source_lesson__thing',
            'target_lesson__thing__time',
            'target_lesson__thing__tag',
        ).get(id=request.data.get('id'), status='active')
    except PermanentCourseChange.DoesNotExist:
        return APIResponse(code=1, msg='Active permanent change does not exist')

    record.source_order.return_time = record.original_source_return_time
    record.source_order.num = record.transferred_lesson_count
    record.source_order.save(update_fields=['return_time', 'num'])
    record.target_order.status = 7
    record.target_order.num = 0
    record.target_order.save(update_fields=['status', 'num'])
    record.target_lesson.students.remove(record.student)
    record.source_lesson.students.add(record.student)
    record.status = 'reverted'
    record.reverted_by = request.user
    record.reverted_time = timezone.now()
    record.save(update_fields=['status', 'reverted_by', 'reverted_time'])
    return APIResponse(code=0, msg='Permanent course change reverted', data=_serialize(record))
