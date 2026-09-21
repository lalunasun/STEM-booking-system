import datetime

from django.db.models import Q

from CSAA.models import (
    AdminTrialSession,
    ClassPassBooking,
    CourseAdjustment,
    DailyStudentAdjustment,
    Order,
    TrialRequest,
)


# Pending payment orders do not reserve a student's schedule yet.
ACTIVE_ORDER_STATUSES = [2, 6]
ACTIVE_TRIAL_STATUSES = ['pending', 'approved', 'scheduled']


def active_trial_reserves_schedule(trial_request):
    if trial_request.package_order:
        return trial_request.package_order.status in ACTIVE_ORDER_STATUSES
    return trial_request.status != 'pending'


def thing_slot_key(thing):
    if not thing or not thing.day or not thing.time_id:
        return None
    return thing.day, thing.time_id


def thing_time_range(thing):
    try:
        start, end = thing.time.time.split('-', 1)
        return (
            datetime.time.fromisoformat(start.strip().zfill(5)),
            datetime.time.fromisoformat(end.strip().zfill(5)),
        )
    except (AttributeError, TypeError, ValueError):
        return None


def things_overlap(first, second):
    if not first or not second or first.day != second.day:
        return False
    first_range = thing_time_range(first)
    second_range = thing_time_range(second)
    if not first_range or not second_range:
        return bool(first.time_id and first.time_id == second.time_id)
    return first_range[0] < second_range[1] and second_range[0] < first_range[1]


def thing_label(thing):
    if not thing:
        return 'Unknown class'

    parts = [thing.title or 'Untitled class']
    if thing.day:
        parts.append(thing.day)
    if thing.time:
        parts.append(thing.time.time)
    if thing.tag:
        parts.append(thing.tag.title)
    return ' | '.join(parts)


def selected_slot_conflict(things):
    seen = []
    for thing in things:
        for existing in seen:
            if things_overlap(existing, thing):
                return (
                    f'Schedule conflict: {thing_label(existing)} and '
                    f'{thing_label(thing)} overlap'
                )
        seen.append(thing)
    return None


def student_slot_conflict(child, thing, exclude_order_id=None, exclude_trial_request_id=None):
    key = thing_slot_key(thing)
    if not child or not key:
        return None

    day, _ = key
    orders = Order.objects.filter(
        child=child,
        status__in=ACTIVE_ORDER_STATUSES,
        thing__day=day,
    ).select_related('thing', 'thing__time', 'thing__tag')
    if exclude_order_id:
        orders = orders.exclude(id=exclude_order_id)

    for existing_order in orders:
        if things_overlap(existing_order.thing, thing):
            return (
                f'Schedule conflict: this student already has '
                f'{thing_label(existing_order.thing)} at this time'
            )

    trial_requests = TrialRequest.objects.filter(
        child=child,
        status__in=ACTIVE_TRIAL_STATUSES,
    ).select_related(
        'package_order',
        'robotics_class',
        'robotics_class__time',
        'robotics_class__tag',
        'coding_class',
        'coding_class__time',
        'coding_class__tag',
    )
    if exclude_trial_request_id:
        trial_requests = trial_requests.exclude(id=exclude_trial_request_id)

    for trial_request in trial_requests:
        if not active_trial_reserves_schedule(trial_request):
            continue
        for trial_thing in [
            trial_request.robotics_class,
            trial_request.coding_class,
        ]:
            if things_overlap(trial_thing, thing):
                return (
                    f'Schedule conflict: this student already has trial '
                    f'{thing_label(trial_thing)} at this time'
                )

    return None


def student_slot_conflict_on_date(
    child,
    thing,
    class_date,
    exclude_order_id=None,
    exclude_trial_request_id=None,
    exclude_daily_adjustment_id=None,
    exclude_class_pass_booking_id=None,
):
    key = thing_slot_key(thing)
    if not child or not key or not class_date:
        return None

    day, _ = key
    orders = Order.objects.filter(
        child=child,
        status__in=ACTIVE_ORDER_STATUSES,
        thing__day=day,
        expect_time__isnull=False,
        return_time__isnull=False,
    ).select_related('thing', 'thing__time', 'thing__tag')
    if exclude_order_id:
        orders = orders.exclude(id=exclude_order_id)

    for order in orders:
        start_date = order.expect_time.date() if hasattr(order.expect_time, 'date') else order.expect_time
        end_date = order.return_time.date() if hasattr(order.return_time, 'date') else order.return_time
        moved_out = DailyStudentAdjustment.objects.filter(
            source_order=order, lesson_date=class_date, status='active',
        )
        if exclude_daily_adjustment_id:
            moved_out = moved_out.exclude(id=exclude_daily_adjustment_id)
        if moved_out.exists():
            continue
        if start_date and end_date and start_date <= class_date <= end_date and things_overlap(order.thing, thing):
            return (
                f'Schedule conflict: this student already has '
                f'{thing_label(order.thing)} at this time'
            )

    makeups = CourseAdjustment.objects.filter(
        student=child,
        request_type='makeup_class',
        status='completed',
        selected_target_date=class_date,
        selected_target_class__day=day,
    ).select_related('selected_target_class', 'selected_target_class__time', 'selected_target_class__tag')
    for makeup in makeups:
        if things_overlap(makeup.selected_target_class, thing):
            return (
                f'Schedule conflict: this student already has makeup '
                f'{thing_label(makeup.selected_target_class)} at this time'
            )

    trial_requests = TrialRequest.objects.filter(
        child=child,
        status__in=ACTIVE_TRIAL_STATUSES,
    ).select_related(
        'package_order',
        'robotics_class',
        'robotics_class__time',
        'robotics_class__tag',
        'coding_class',
        'coding_class__time',
        'coding_class__tag',
    )
    if exclude_trial_request_id:
        trial_requests = trial_requests.exclude(id=exclude_trial_request_id)

    for trial_request in trial_requests:
        if not active_trial_reserves_schedule(trial_request):
            continue
        for trial_thing in [
            trial_request.robotics_class,
            trial_request.coding_class,
        ]:
            if not trial_thing or not trial_request.package_order or not trial_request.package_order.order_time:
                continue
            base_date = trial_request.package_order.order_time.date()
            try:
                trial_day = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'].index(trial_thing.day)
            except ValueError:
                continue
            trial_date = base_date + datetime.timedelta(days=(trial_day - base_date.weekday()) % 7)
            if trial_date == class_date and things_overlap(trial_thing, thing):
                return (
                    f'Schedule conflict: this student already has trial '
                    f'{thing_label(trial_thing)} at this time'
                )

    target_range = thing_time_range(thing)
    if target_range:
        admin_trial = AdminTrialSession.objects.filter(
            student=child, session_date=class_date, status='active',
            starts_at__lt=target_range[1], ends_at__gt=target_range[0],
        ).first()
        if admin_trial:
            return 'Schedule conflict: this student already has an administrator-booked trial at this time'

    moves = DailyStudentAdjustment.objects.filter(
        student=child, adjustment_type='move', status='active',
    ).filter(
        Q(target_lesson_date=class_date) |
        Q(target_lesson_date__isnull=True, lesson_date=class_date),
    ).select_related('target_lesson__thing__time', 'target_lesson__thing__tag')
    if exclude_daily_adjustment_id:
        moves = moves.exclude(id=exclude_daily_adjustment_id)
    for move in moves:
        if things_overlap(move.target_lesson.thing, thing):
            return f'Schedule conflict: this student already has rescheduled {thing_label(move.target_lesson.thing)} at this time'

    class_passes = ClassPassBooking.objects.filter(
        child=child, requested_date=class_date, status__in=['approved', 'completed'],
    ).select_related('requested_class__time', 'requested_class__tag')
    if exclude_class_pass_booking_id:
        class_passes = class_passes.exclude(id=exclude_class_pass_booking_id)
    for booking in class_passes:
        if things_overlap(booking.requested_class, thing):
            return f'Schedule conflict: this student already has class pass {thing_label(booking.requested_class)} at this time'

    return None
