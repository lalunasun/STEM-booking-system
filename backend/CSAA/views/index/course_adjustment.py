import datetime
import re

from rest_framework.decorators import api_view

from CSAA.handler import APIResponse
from CSAA.models import CourseAdjustment, Order
from CSAA.serializers import CourseAdjustmentSerializer


DAY_LABELS = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']


def _parse_lesson_start(lesson_date, time_label):
    match = re.search(r'(\d{1,2}):(\d{2})', time_label or '')
    hour = int(match.group(1)) if match else 0
    minute = int(match.group(2)) if match else 0
    return datetime.datetime.combine(lesson_date, datetime.time(hour, minute))


@api_view(['POST'])
def create_cancel_request(request):
    order_id = request.data.get('order_id')
    user_id = request.data.get('user_id')
    lesson_date_text = request.data.get('lesson_date')
    parent_note = request.data.get('parent_note', '')

    if not order_id or not user_id or not lesson_date_text:
        return APIResponse(code=1, msg='Missing order, user, or lesson date')

    try:
        lesson_date = datetime.datetime.strptime(lesson_date_text, '%Y-%m-%d').date()
        order = Order.objects.select_related('user', 'child', 'thing', 'thing__time', 'thing__tag', 'term').get(
            pk=order_id,
            user_id=user_id,
        )
    except ValueError:
        return APIResponse(code=1, msg='Invalid lesson date')
    except Order.DoesNotExist:
        return APIResponse(code=1, msg='Order not found')

    if order.status not in [2, 6]:
        return APIResponse(code=1, msg='Only paid or scheduled orders can request class cancellation')
    if not order.child or not order.thing:
        return APIResponse(code=1, msg='Order is missing student or class information')
    if order.expect_time and lesson_date < order.expect_time.date():
        return APIResponse(code=1, msg='Lesson date is before the term starts')
    if order.return_time and lesson_date > order.return_time.date():
        return APIResponse(code=1, msg='Lesson date is after the term ends')

    if order.thing.day:
        expected_day = DAY_LABELS[lesson_date.weekday()]
        if expected_day.lower() != order.thing.day.lower():
            return APIResponse(code=1, msg=f'Selected date must be a {order.thing.day}')

    lesson_start = _parse_lesson_start(lesson_date, order.thing.time.time if order.thing.time else '')
    if lesson_start - datetime.datetime.now() < datetime.timedelta(hours=48):
        return APIResponse(code=1, msg='Cancel requests must be submitted at least 48 hours before class. Please call or email admin for special cases.')

    existing = CourseAdjustment.objects.filter(
        original_order=order,
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
        original_class=order.thing,
        original_lesson_date=lesson_date,
        original_day=order.thing.day,
        original_time=order.thing.time.time if order.thing.time else None,
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
