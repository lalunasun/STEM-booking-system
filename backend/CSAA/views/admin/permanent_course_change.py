import datetime
import uuid

from django.db import transaction
from django.utils import timezone
from django.utils.dateparse import parse_date
from rest_framework.decorators import api_view, authentication_classes

from CSAA.auth.authentication import AdminTokenAuthtication
from CSAA.course_conflicts import student_slot_conflict_on_date
from CSAA.handler import APIResponse
from CSAA.models import Lesson, Order, PermanentCourseChange, Tag, Thing, Time
from CSAA.room_permissions import candidate_classes, course_allowed
from CSAA.time_slots import time_slot_key
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


def _source_end_date(effective_date):
    """End the old enrollment before the week containing the first new class."""
    start_of_target_week = effective_date - datetime.timedelta(days=effective_date.weekday())
    return start_of_target_week - datetime.timedelta(days=1)


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


def _source_date(params, effective_date):
    raw = params.get('source_date')
    if raw is None:
        return effective_date
    try:
        return parse_date(str(raw))
    except ValueError:
        return None


def _same_class_slot(left, right):
    return (left.title.strip().casefold(), left.tag_id, left.day, time_slot_key(left.time)) == (
        right.title.strip().casefold(), right.tag_id, right.day, time_slot_key(right.time)
    )


def _target_lesson_from_slot(source_order, course, effective_date, room_id, time_id):
    target_day = next(day for day, index in DAY_INDEX.items() if index == effective_date.weekday())
    try:
        room_id = int(room_id)
        time_id = int(time_id)
        Tag.objects.select_for_update().get(pk=room_id)
        Time.objects.get(pk=time_id)
    except (Tag.DoesNotExist, Time.DoesNotExist, TypeError, ValueError):
        return None, 'Target room or time does not exist'

    target_thing = next((
        thing for thing in candidate_classes(
            source_order.term, course, target_day, time_id,
        )
        if thing.tag_id == room_id
    ), None)
    if target_thing is None:
        return None, 'This course is not allowed in the selected room and time'

    if target_thing.pk is None:
        template = Thing.objects.filter(
            title__iexact=target_thing.title,
            status='0',
        ).first()
        if template:
            target_thing.classification = template.classification
            target_thing.cover = template.cover
            target_thing.description = template.description
            target_thing.price = template.price
        target_thing.save()
    target_lesson, _ = Lesson.objects.get_or_create(thing=target_thing)
    return target_lesson, None


def _serialize(record):
    return {
        'id': record.id,
        'student_id': record.student_id,
        'student_name': record.student.name,
        'effective_date': record.effective_date.strftime('%Y-%m-%d'),
        'source_end_date': record.source_order.return_time.date().isoformat(),
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

    source_date = _source_date(request.GET, effective_date)
    if not source_date:
        return APIResponse(code=1, msg='A valid original class date is required')
    source_order = _source_order(student_id, source_lesson_id, source_date)
    if not source_order:
        return APIResponse(code=1, msg='No active source enrollment exists on the effective date')

    course = request.GET.get('course', '').strip()
    if not course:
        rows = Lesson.objects.filter(
            thing__status='0', thing__time__isnull=False,
            thing__tag__isnull=False, thing__day__isnull=False,
        ).exclude(id=source_lesson_id).values_list(
            'thing__title', 'thing__day', 'thing__tag_id',
        ).distinct()
        end_date = source_order.return_time.date()
        data = []
        seen = set()
        for title, day, room_id in rows:
            if not course_allowed(room_id, source_order.term, title, day):
                continue
            day_index = DAY_INDEX.get(day)
            if day_index is None:
                continue
            first_date = effective_date + datetime.timedelta(days=(day_index - effective_date.weekday()) % 7)
            key = (title.casefold(), day)
            if first_date and first_date <= end_date and key not in seen:
                seen.add(key)
                data.append({
                    'class_name': title, 'day': day,
                    'first_class_date': first_date.strftime('%Y-%m-%d'),
                    'enrollment_end_date': end_date.strftime('%Y-%m-%d'),
                })
        source_title = source_order.thing.title
        for thing in candidate_classes(source_order.term, source_title):
            first_date = _first_class_date(thing, effective_date)
            key = (source_title.casefold(), thing.day)
            if first_date and first_date <= end_date and key not in seen:
                seen.add(key)
                data.append({
                    'class_name': source_title,
                    'day': thing.day,
                    'first_class_date': first_date.strftime('%Y-%m-%d'),
                    'enrollment_end_date': end_date.strftime('%Y-%m-%d'),
                })
        return APIResponse(code=0, msg='Query successful', data=data)

    target_day = next(day for day, index in DAY_INDEX.items() if index == effective_date.weekday())
    data = []
    for thing in candidate_classes(source_order.term, course, target_day):
        lesson = (
            Lesson.objects.filter(thing=thing).order_by('id').first()
            if thing.pk else None
        )
        if _same_class_slot(thing, source_order.thing):
            continue
        first_date = _first_class_date(thing, effective_date)
        if not first_date or first_date > source_order.return_time.date():
            continue
        capacity = thing.tag.seat or 0
        occupancy_lesson = lesson or Lesson(thing=thing)
        remaining = max(int(capacity) - _occupied_count(occupancy_lesson, first_date), 0) if capacity else None
        data.append({
            'lesson_id': lesson.id if lesson else None,
            'room_id': thing.tag_id,
            'time_id': thing.time_id,
            'class_name': thing.title,
            'day': thing.day,
            'time': thing.time.time if thing.time else None,
            'room': thing.tag.title if thing.tag else None,
            'capacity': thing.tag.seat if thing.tag else 0,
            'remaining': remaining,
            'first_class_date': first_date.strftime('%Y-%m-%d'),
            'enrollment_end_date': source_order.return_time.date().strftime('%Y-%m-%d'),
        })
    return APIResponse(code=0, msg='Query successful', data=data)


@api_view(['GET'])
@authentication_classes([AdminTokenAuthtication])
def list_api(request):
    records = PermanentCourseChange.objects.filter(
        status='active',
    ).select_related(
        'student',
        'source_order',
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
    target_room_id = request.data.get('target_room_id')
    target_time_id = request.data.get('target_time_id')
    course = str(request.data.get('course', '')).strip()
    reason = str(request.data.get('reason', '')).strip()
    if not effective_date:
        return APIResponse(code=1, msg='A valid effective date is required')

    source_date = _source_date(request.data, effective_date)
    if not source_date:
        return APIResponse(code=1, msg='A valid original class date is required')
    source_order = _source_order(student_id, source_lesson_id, source_date)
    if not source_order:
        return APIResponse(code=1, msg='No active source enrollment exists on the effective date')
    if request.data.get('source_date') is not None and DAY_INDEX.get(source_order.thing.day) != source_date.weekday():
        return APIResponse(code=1, msg='Original class date must match the current class weekday')
    if PermanentCourseChange.objects.filter(
        source_order=source_order,
        status='active',
    ).exists():
        return APIResponse(code=1, msg='This enrollment already has an active permanent change')

    try:
        source_lesson = Lesson.objects.select_related('thing').get(id=source_lesson_id)
    except Lesson.DoesNotExist:
        return APIResponse(code=1, msg='Source class does not exist')
    if target_lesson_id:
        try:
            target_lesson = Lesson.objects.select_related(
                'thing',
                'thing__time',
                'thing__tag',
            ).get(id=target_lesson_id, thing__status='0')
        except Lesson.DoesNotExist:
            return APIResponse(code=1, msg='Target class does not exist')
    else:
        target_lesson, target_error = _target_lesson_from_slot(
            source_order,
            course or source_lesson.thing.title,
            effective_date,
            target_room_id,
            target_time_id,
        )
        if target_error:
            return APIResponse(code=1, msg=target_error)
    if _same_class_slot(source_lesson.thing, target_lesson.thing):
        transaction.set_rollback(True)
        return APIResponse(code=1, msg='Source and target classes are the same')
    if not course_allowed(
        target_lesson.thing.tag_id,
        source_order.term,
        target_lesson.thing.title,
        target_lesson.thing.day,
    ):
        transaction.set_rollback(True)
        return APIResponse(code=1, msg=f'{target_lesson.thing.tag.title} has no classes on this weekday')

    first_target_date = _first_class_date(target_lesson.thing, effective_date)
    if not first_target_date or first_target_date > source_order.return_time.date():
        transaction.set_rollback(True)
        return APIResponse(code=1, msg='The target class has no remaining lesson in this enrollment period')
    if first_target_date < source_order.expect_time.date():
        transaction.set_rollback(True)
        return APIResponse(code=1, msg='The target date must be within the enrollment period')
    capacity = int(target_lesson.thing.tag.seat or 0)
    if capacity and _occupied_count(target_lesson, first_target_date) >= capacity:
        transaction.set_rollback(True)
        return APIResponse(code=1, msg=f'{target_lesson.thing.tag.title} is full')
    conflict = student_slot_conflict_on_date(
        source_order.child,
        target_lesson.thing,
        first_target_date,
        exclude_order_id=source_order.id,
    )
    if conflict:
        transaction.set_rollback(True)
        return APIResponse(code=1, msg=conflict)

    original_return_time = source_order.return_time
    transferred_count = source_order.num
    # Keep the current week's old class, but prevent old and new schedules from
    # both appearing in the week that contains the first target class.
    source_order.return_time = _at_end(_source_end_date(effective_date))
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
