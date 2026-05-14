from CSAA.models import CourseAdjustment, Order, TrialRequest


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
    seen = {}
    for thing in things:
        key = thing_slot_key(thing)
        if not key:
            continue
        if key in seen:
            return (
                f'Schedule conflict: {thing_label(seen[key])} and '
                f'{thing_label(thing)} are at the same time'
            )
        seen[key] = thing
    return None


def student_slot_conflict(child, thing, exclude_order_id=None, exclude_trial_request_id=None):
    key = thing_slot_key(thing)
    if not child or not key:
        return None

    day, time_id = key
    orders = Order.objects.filter(
        child=child,
        status__in=ACTIVE_ORDER_STATUSES,
        thing__day=day,
        thing__time_id=time_id,
    ).select_related('thing', 'thing__time', 'thing__tag')
    if exclude_order_id:
        orders = orders.exclude(id=exclude_order_id)

    existing_order = orders.first()
    if existing_order:
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
        'math_class',
        'math_class__time',
        'math_class__tag',
    )
    if exclude_trial_request_id:
        trial_requests = trial_requests.exclude(id=exclude_trial_request_id)

    for trial_request in trial_requests:
        if not active_trial_reserves_schedule(trial_request):
            continue
        for trial_thing in [
            trial_request.robotics_class,
            trial_request.coding_class,
            trial_request.math_class,
        ]:
            if thing_slot_key(trial_thing) == key:
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
):
    key = thing_slot_key(thing)
    if not child or not key or not class_date:
        return None

    day, time_id = key
    orders = Order.objects.filter(
        child=child,
        status__in=ACTIVE_ORDER_STATUSES,
        thing__day=day,
        thing__time_id=time_id,
        expect_time__isnull=False,
        return_time__isnull=False,
    ).select_related('thing', 'thing__time', 'thing__tag')
    if exclude_order_id:
        orders = orders.exclude(id=exclude_order_id)

    for order in orders:
        start_date = order.expect_time.date() if hasattr(order.expect_time, 'date') else order.expect_time
        end_date = order.return_time.date() if hasattr(order.return_time, 'date') else order.return_time
        if start_date and end_date and start_date <= class_date <= end_date:
            return (
                f'Schedule conflict: this student already has '
                f'{thing_label(order.thing)} at this time'
            )

    makeup = CourseAdjustment.objects.filter(
        student=child,
        request_type='makeup_class',
        status='completed',
        selected_target_date=class_date,
        selected_target_class__day=day,
        selected_target_class__time_id=time_id,
    ).select_related('selected_target_class', 'selected_target_class__time', 'selected_target_class__tag').first()
    if makeup:
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
        'math_class',
        'math_class__time',
        'math_class__tag',
    )
    if exclude_trial_request_id:
        trial_requests = trial_requests.exclude(id=exclude_trial_request_id)

    for trial_request in trial_requests:
        if not active_trial_reserves_schedule(trial_request):
            continue
        for trial_thing in [
            trial_request.robotics_class,
            trial_request.coding_class,
            trial_request.math_class,
        ]:
            if thing_slot_key(trial_thing) == key:
                return (
                    f'Schedule conflict: this student already has trial '
                    f'{thing_label(trial_thing)} at this time'
                )

    return None
