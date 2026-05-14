import datetime
import re

from rest_framework.decorators import api_view

from CSAA.handler import APIResponse
from CSAA.models import CourseAdjustment, Order, TrialRequest
from CSAA.serializers import CourseAdjustmentSerializer


DAY_LABELS = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
DAY_INDEX = {
    'Mon': 0,
    'Tue': 1,
    'Wed': 2,
    'Thu': 3,
    'Fri': 4,
    'Sat': 5,
    'Sun': 6,
}


def _parse_lesson_start(lesson_date, time_label):
    match = re.search(r'(\d{1,2}):(\d{2})', time_label or '')
    hour = int(match.group(1)) if match else 0
    minute = int(match.group(2)) if match else 0
    return datetime.datetime.combine(lesson_date, datetime.time(hour, minute))


def _next_trial_date(order, thing):
    if not order or not thing or thing.day not in DAY_INDEX:
        return None

    base_date = order.order_time.date() if order.order_time else datetime.date.today()
    days_ahead = (DAY_INDEX[thing.day] - base_date.weekday()) % 7
    return base_date + datetime.timedelta(days=days_ahead)


def _trial_class_from_request(trial_request, class_id):
    for thing in [
        trial_request.robotics_class,
        trial_request.coding_class,
        trial_request.math_class,
    ]:
        if thing and str(thing.id) == str(class_id):
            return thing
    return None


@api_view(['POST'])
def create_cancel_request(request):
    order_id = request.data.get('order_id')
    user_id = request.data.get('user_id')
    lesson_date_text = request.data.get('lesson_date')
    trial_class_id = request.data.get('trial_class_id')
    parent_note = request.data.get('parent_note', '')

    if not order_id or not user_id:
        return APIResponse(code=1, msg='Missing order or user')

    try:
        order = Order.objects.select_related('user', 'child', 'thing', 'thing__time', 'thing__tag', 'term').get(
            pk=order_id,
            user_id=user_id,
        )
    except Order.DoesNotExist:
        return APIResponse(code=1, msg='Order not found')

    trial_request = TrialRequest.objects.filter(package_order=order).select_related(
        'robotics_class',
        'robotics_class__time',
        'robotics_class__tag',
        'coding_class',
        'coding_class__time',
        'coding_class__tag',
        'math_class',
        'math_class__time',
        'math_class__tag',
    ).first()

    selected_class = order.thing
    if trial_request:
        if not trial_class_id:
            return APIResponse(code=1, msg='Please select the trial class to cancel')
        selected_class = _trial_class_from_request(trial_request, trial_class_id)
        if not selected_class:
            return APIResponse(code=1, msg='Selected trial class is invalid')
        lesson_date = _next_trial_date(order, selected_class)
        if not lesson_date:
            return APIResponse(code=1, msg='Trial class date cannot be determined')
    else:
        if not lesson_date_text:
            return APIResponse(code=1, msg='Missing lesson date')
        try:
            lesson_date = datetime.datetime.strptime(lesson_date_text, '%Y-%m-%d').date()
        except ValueError:
            return APIResponse(code=1, msg='Invalid lesson date')

    if order.status not in [2, 6]:
        return APIResponse(code=1, msg='Only paid or scheduled orders can request class cancellation')
    if not order.child or not selected_class:
        return APIResponse(code=1, msg='Order is missing student or class information')
    if not trial_request and order.expect_time and lesson_date < order.expect_time.date():
        return APIResponse(code=1, msg='Lesson date is before the term starts')
    if not trial_request and order.return_time and lesson_date > order.return_time.date():
        return APIResponse(code=1, msg='Lesson date is after the term ends')

    if selected_class.day:
        expected_day = DAY_LABELS[lesson_date.weekday()]
        if expected_day.lower() != selected_class.day.lower():
            return APIResponse(code=1, msg=f'Selected date must be a {selected_class.day}')

    lesson_start = _parse_lesson_start(lesson_date, selected_class.time.time if selected_class.time else '')
    if lesson_start - datetime.datetime.now() < datetime.timedelta(hours=48):
        return APIResponse(code=1, msg='Cancel requests must be submitted at least 48 hours before class. Please call or email admin for special cases.')

    existing = CourseAdjustment.objects.filter(
        original_order=order,
        original_class=selected_class,
        original_lesson_date=lesson_date,
        request_type='cancel_class',
        status__in=['pending', 'approved', 'completed'],
    ).first()
    if existing:
        return APIResponse(code=1, msg='A cancel request already exists for this class date')

    adjustment = CourseAdjustment.objects.create(
        student=order.child,
        parent=order.user,
        original_order=order,
        original_class=selected_class,
        original_lesson_date=lesson_date,
        original_day=selected_class.day,
        original_time=selected_class.time.time if selected_class.time else None,
        original_term=order.term,
        request_type='cancel_class',
        request_reason=parent_note,
        request_source='parent',
        status='pending',
        parent_note=parent_note,
        admin_note='Email notification pending: parent submitted a cancel class request.',
    )

    serializer = CourseAdjustmentSerializer(adjustment)
    return APIResponse(code=0, msg='Cancel request submitted', data=serializer.data)
