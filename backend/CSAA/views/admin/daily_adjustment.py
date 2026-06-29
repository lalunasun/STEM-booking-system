import json

from django.db import transaction
from django.utils import timezone
from django.utils.dateparse import parse_date
from rest_framework.decorators import api_view, authentication_classes

from CSAA.auth.authentication import AdminTokenAuthtication
from CSAA.course_conflicts import student_slot_conflict_on_date
from CSAA.handler import APIResponse
from CSAA.models import (
    CourseAdjustment,
    DailyStudentAdjustment,
    Lesson,
    Order,
    StudentLessonNote,
    TrialRequest,
)


def _active_order(student_id, lesson, lesson_date):
    return Order.objects.filter(
        child_id=student_id,
        thing=lesson.thing,
        status=6,
        expect_time__date__lte=lesson_date,
        return_time__date__gte=lesson_date,
    ).select_related('child', 'thing', 'thing__time', 'thing__tag').first()


def _active_move_into(student_id, lesson, lesson_date):
    return DailyStudentAdjustment.objects.filter(
        student_id=student_id,
        target_lesson=lesson,
        lesson_date=lesson_date,
        status='active',
        adjustment_type='move',
    ).select_related(
        'student',
        'source_order',
        'source_order__child',
        'source_lesson__thing',
        'target_lesson__thing',
    ).first()


def _same_room_slot(left, right):
    if not left or not right:
        return False
    left_thing = left.thing
    right_thing = right.thing
    return (
        left_thing.tag_id == right_thing.tag_id and
        left_thing.day == right_thing.day and
        left_thing.time_id == right_thing.time_id
    )


def _occupied_count(lesson, lesson_date):
    same_room_things = Lesson.objects.filter(
        thing__tag=lesson.thing.tag,
        thing__day=lesson.thing.day,
        thing__time=lesson.thing.time,
        thing__status='0',
    ).values_list('thing_id', flat=True)
    same_room_lessons = Lesson.objects.filter(
        thing_id__in=same_room_things,
    ).values_list('id', flat=True)
    regular = Order.objects.filter(
        thing_id__in=same_room_things,
        status=6,
        child__isnull=False,
        expect_time__date__lte=lesson_date,
        return_time__date__gte=lesson_date,
    ).count()
    canceled = CourseAdjustment.objects.filter(
        original_class_id__in=same_room_things,
        original_lesson_date=lesson_date,
        request_type='cancel_class',
        status='approved',
    ).count()
    makeup = CourseAdjustment.objects.filter(
        selected_target_class_id__in=same_room_things,
        selected_target_date=lesson_date,
        request_type='makeup_class',
        status='completed',
    ).count()
    trials = TrialRequest.objects.filter(
        package_order__status__in=[2, 6],
        status__in=['approved', 'scheduled'],
    ).filter(
        robotics_class_id__in=same_room_things,
    ).count()
    trials += TrialRequest.objects.filter(
        package_order__status__in=[2, 6],
        status__in=['approved', 'scheduled'],
        coding_class_id__in=same_room_things,
    ).count()
    move_out = DailyStudentAdjustment.objects.filter(
        source_lesson_id__in=same_room_lessons,
        lesson_date=lesson_date,
        status='active',
        adjustment_type__in=['move', 'sick_leave'],
    ).count()
    move_in = DailyStudentAdjustment.objects.filter(
        target_lesson_id__in=same_room_lessons,
        lesson_date=lesson_date,
        status='active',
        adjustment_type='move',
    ).count()
    return max(regular - canceled - move_out, 0) + makeup + trials + move_in


def _serialize(record):
    return {
        'id': record.id,
        'student_id': record.student_id,
        'student_name': record.student.name,
        'lesson_date': record.lesson_date.strftime('%Y-%m-%d'),
        'adjustment_type': record.adjustment_type,
        'source_lesson_id': record.source_lesson_id,
        'source_class': record.source_lesson.thing.title,
        'target_lesson_id': record.target_lesson_id,
        'target_class': record.target_lesson.thing.title if record.target_lesson else None,
        'lesson_count_delta': record.lesson_count_delta,
        'reason': record.reason,
        'status': record.status,
    }


@api_view(['GET'])
@authentication_classes([AdminTokenAuthtication])
def list_api(request):
    lesson_date = parse_date(request.GET.get('date', ''))
    if not lesson_date:
        return APIResponse(code=1, msg='A valid lesson date is required')
    records = DailyStudentAdjustment.objects.filter(
        lesson_date=lesson_date,
        status='active',
    ).select_related(
        'student',
        'source_lesson__thing',
        'target_lesson__thing',
    ).order_by('created_time')
    return APIResponse(code=0, msg='Query successful', data=[_serialize(record) for record in records])


@api_view(['POST'])
@authentication_classes([AdminTokenAuthtication])
@transaction.atomic
def save_batch(request):
    lesson_date = parse_date(str(request.data.get('lesson_date', '')))
    try:
        actions = json.loads(request.data.get('actions', '[]'))
    except (TypeError, ValueError):
        actions = []
    if not lesson_date or not actions:
        return APIResponse(code=1, msg='A lesson date and at least one adjustment are required')

    created = []
    for action in actions:
        adjustment_type = action.get('type')
        student_id = action.get('student_id')
        source_lesson_id = action.get('source_lesson_id')
        target_lesson_id = action.get('target_lesson_id')
        reason = str(action.get('reason', '')).strip()

        try:
            source_lesson = Lesson.objects.select_related(
                'thing',
                'thing__time',
                'thing__tag',
            ).get(id=source_lesson_id, thing__status='0')
        except Lesson.DoesNotExist:
            return APIResponse(code=1, msg='Source class does not exist')

        existing_move_into_source = _active_move_into(student_id, source_lesson, lesson_date)
        source_order = _active_order(student_id, source_lesson, lesson_date)
        if not source_order and existing_move_into_source:
            source_order = existing_move_into_source.source_order
        if not source_order:
            return APIResponse(code=1, msg='Student is not scheduled in the source class on this date')
        existing_adjustment = DailyStudentAdjustment.objects.select_for_update().filter(
            student_id=student_id,
            lesson_date=lesson_date,
            status='active',
        ).first()
        can_retarget_existing_move = (
            adjustment_type == 'move' and
            existing_adjustment and
            existing_adjustment.adjustment_type == 'move' and
            existing_adjustment.target_lesson_id == source_lesson.id
        )
        if existing_adjustment and not can_retarget_existing_move:
            return APIResponse(code=1, msg=f'{source_order.child.name} already has a daily adjustment')

        if adjustment_type == 'move':
            try:
                target_lesson = Lesson.objects.select_related(
                    'thing',
                    'thing__time',
                    'thing__tag',
                ).get(id=target_lesson_id, thing__status='0')
            except Lesson.DoesNotExist:
                return APIResponse(code=1, msg='Target class does not exist')
            expected_day = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'][lesson_date.weekday()]
            if target_lesson.thing.day != expected_day:
                return APIResponse(code=1, msg='Target class is not available on this date')
            if source_lesson.id == target_lesson.id:
                return APIResponse(code=1, msg='Source and target classes are the same')
            capacity = int(target_lesson.thing.tag.seat or 0)
            is_same_current_slot = bool(existing_move_into_source and _same_room_slot(source_lesson, target_lesson))
            if capacity and not is_same_current_slot and _occupied_count(target_lesson, lesson_date) >= capacity:
                return APIResponse(code=1, msg=f'{target_lesson.thing.tag.title} is full')
            conflict = student_slot_conflict_on_date(
                source_order.child,
                target_lesson.thing,
                lesson_date,
                exclude_order_id=source_order.id,
            )
            if conflict:
                return APIResponse(code=1, msg=conflict)
            if can_retarget_existing_move:
                record = existing_adjustment
                old_target_lesson = record.target_lesson
                record.target_lesson = target_lesson
                record.reason = reason
                record.created_by = request.user
                record.save(update_fields=['target_lesson', 'reason', 'created_by'])
                StudentLessonNote.objects.filter(
                    student=source_order.child,
                    lesson=old_target_lesson,
                    lesson_date=lesson_date,
                ).update(lesson=target_lesson)
            else:
                record = DailyStudentAdjustment.objects.create(
                    student=source_order.child,
                    lesson_date=lesson_date,
                    adjustment_type='move',
                    source_lesson=source_lesson,
                    target_lesson=target_lesson,
                    source_order=source_order,
                    reason=reason,
                    created_by=request.user,
                )
                StudentLessonNote.objects.filter(
                    student=source_order.child,
                    lesson=source_lesson,
                    lesson_date=lesson_date,
                ).update(lesson=target_lesson)
        elif adjustment_type == 'sick_leave':
            deduct_lesson = bool(action.get('deduct_lesson'))
            delta = 0
            if deduct_lesson:
                if source_order.num <= 0:
                    return APIResponse(code=1, msg='Remaining lesson count cannot go below zero')
                source_order.num -= 1
                source_order.save(update_fields=['num'])
                delta = -1
            record = DailyStudentAdjustment.objects.create(
                student=source_order.child,
                lesson_date=lesson_date,
                adjustment_type='sick_leave',
                source_lesson=source_lesson,
                source_order=source_order,
                lesson_count_delta=delta,
                reason=reason,
                created_by=request.user,
            )
        else:
            return APIResponse(code=1, msg='Unsupported adjustment type')
        created.append(_serialize(record))

    return APIResponse(code=0, msg='Adjustments saved', data=created)


@api_view(['POST'])
@authentication_classes([AdminTokenAuthtication])
@transaction.atomic
def revert(request):
    record_id = request.data.get('id')
    try:
        record = DailyStudentAdjustment.objects.select_for_update().select_related(
            'source_order',
            'student',
            'source_lesson__thing',
            'target_lesson__thing',
        ).get(id=record_id, status='active')
    except DailyStudentAdjustment.DoesNotExist:
        return APIResponse(code=1, msg='Active adjustment does not exist')

    if record.lesson_count_delta and record.source_order:
        record.source_order.num -= record.lesson_count_delta
        record.source_order.save(update_fields=['num'])
    if record.adjustment_type == 'move' and record.target_lesson:
        StudentLessonNote.objects.filter(
            student=record.student,
            lesson=record.target_lesson,
            lesson_date=record.lesson_date,
        ).update(lesson=record.source_lesson)
    record.status = 'reverted'
    record.reverted_by = request.user
    record.reverted_time = timezone.now()
    record.save(update_fields=['status', 'reverted_by', 'reverted_time'])
    return APIResponse(code=0, msg='Adjustment reverted', data=_serialize(record))
