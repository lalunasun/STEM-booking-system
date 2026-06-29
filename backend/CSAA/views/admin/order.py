import datetime

from django.utils import timezone
from rest_framework.decorators import api_view, authentication_classes

from CSAA import utils
from CSAA.auth.authentication import AdminTokenAuthtication
from CSAA.course_conflicts import selected_slot_conflict, student_slot_conflict
from CSAA.handler import APIResponse
from CSAA.models import Child, Lesson, Order, Term, Thing, TrialRequest
from CSAA.serializers import OrderSerializer


def _active_room_count(thing, exclude_order_id=None):
    if not thing or not thing.tag or not thing.day or not thing.time:
        return 0

    same_room_things = Thing.objects.filter(tag=thing.tag, day=thing.day, time=thing.time)
    orders = Order.objects.filter(
        thing__in=same_room_things,
        child__isnull=False,
        status__in=[2, 6],
        trial_package_requests__isnull=True,
    )
    if exclude_order_id:
        orders = orders.exclude(id=exclude_order_id)
    return orders.count()


def _validate_normal_order_capacity(order):
    thing = order.thing
    if not thing or not thing.tag or thing.tag.seat is None:
        return None

    if _active_room_count(thing, exclude_order_id=order.id) >= int(thing.tag.seat):
        time_label = thing.time.time if thing.time else ''
        return f'{thing.title} is full for {thing.day} {time_label}'
    return None


@api_view(['GET'])
def list_api(request):
    orders = Order.objects.select_related(
        'user',
        'child',
        'thing',
        'thing__time',
        'thing__tag',
        'term',
    ).all().order_by('-order_time')
    serializer = OrderSerializer(orders, many=True)
    return APIResponse(code=0, msg='Success', data=serializer.data)


@api_view(['POST'])
@authentication_classes([AdminTokenAuthtication])
def create(request):
    data = request.data.copy()

    if not data.get('user') or not data.get('thing') or not data.get('count'):
        return APIResponse(code=1, msg='Order data is invalid')

    try:
        thing = Thing.objects.get(pk=data.get('thing'))
        child = Child.objects.get(pk=data.get('child')) if data.get('child') else None
    except (Thing.DoesNotExist, Child.DoesNotExist, TypeError, ValueError):
        return APIResponse(code=1, msg='Order data is invalid')

    conflict = student_slot_conflict(child, thing)
    if conflict:
        return APIResponse(code=1, msg=conflict)

    data['order_number'] = str(utils.get_timestamp())
    data['status'] = data.get('status') or '1'
    data['create_time'] = datetime.datetime.now()

    serializer = OrderSerializer(data=data)
    if serializer.is_valid():
        serializer.save()
        return APIResponse(code=0, msg='Created', data=serializer.data)

    print(serializer.errors)
    return APIResponse(code=1, msg='Create failed')


@api_view(['POST'])
@authentication_classes([AdminTokenAuthtication])
def update(request):
    try:
        order = Order.objects.select_related('child', 'thing', 'term').get(
            pk=request.GET.get('id', -1),
        )
    except Order.DoesNotExist:
        return APIResponse(code=1, msg='Order does not exist')

    if order.status != 1:
        return APIResponse(code=1, msg='Only pending payment orders can be edited')

    if TrialRequest.objects.filter(package_order=order).exists():
        protected_fields = {'child', 'thing', 'term', 'num'}
        if protected_fields.intersection(set(request.data.keys())):
            return APIResponse(code=1, msg='Trial package class details should be edited from the trial request')

    data = request.data.copy()
    update_fields = []

    if data.get('child'):
        try:
            child = Child.objects.select_related('parent').get(pk=data.get('child'))
        except (Child.DoesNotExist, TypeError, ValueError):
            return APIResponse(code=1, msg='Student does not exist')
        order.child = child
        order.user = child.parent
        order.receiver_phone = child.parent.mobile if child.parent else order.receiver_phone
        update_fields.extend(['child', 'user', 'receiver_phone'])

    if data.get('thing'):
        try:
            order.thing = Thing.objects.get(pk=data.get('thing'))
        except (Thing.DoesNotExist, TypeError, ValueError):
            return APIResponse(code=1, msg='Class does not exist')
        update_fields.append('thing')

    if data.get('term'):
        try:
            term = Term.objects.get(pk=data.get('term'))
        except (Term.DoesNotExist, TypeError, ValueError):
            return APIResponse(code=1, msg='Term does not exist')
        order.term = term
        order.expect_time = term.expect_time
        order.return_time = term.return_time
        update_fields.extend(['term', 'expect_time', 'return_time'])

    if data.get('num') not in [None, '']:
        try:
            order.num = int(data.get('num'))
        except (TypeError, ValueError):
            return APIResponse(code=1, msg='Lessons must be a number')
        update_fields.append('num')

    if data.get('amount') not in [None, '']:
        order.amount = str(data.get('amount')).strip()
        update_fields.append('amount')

    if 'remark' in data:
        order.remark = str(data.get('remark') or '').strip()
        update_fields.append('remark')

    if order.child and order.thing:
        conflict = student_slot_conflict(order.child, order.thing, exclude_order_id=order.id)
        if conflict:
            return APIResponse(code=1, msg=conflict)

    if update_fields:
        order.save(update_fields=list(dict.fromkeys(update_fields)))

    serializer = OrderSerializer(order)
    return APIResponse(code=0, msg='Order updated', data=serializer.data)


@api_view(['POST'])
@authentication_classes([AdminTokenAuthtication])
def mark_paid(request):
    try:
        order = Order.objects.select_related('thing', 'child').get(pk=request.GET.get('id', -1))
    except Order.DoesNotExist:
        return APIResponse(code=1, msg='Order does not exist')

    if order.status != 1:
        return APIResponse(code=1, msg='Only pending payment orders can be confirmed')

    trial_request = TrialRequest.objects.filter(package_order=order).first()
    if not trial_request:
        capacity_error = _validate_normal_order_capacity(order)
        if capacity_error:
            return APIResponse(code=1, msg=capacity_error)

    order.status = 2
    order.pay_time = timezone.now()
    order.save(update_fields=['status', 'pay_time'])

    if trial_request and trial_request.status == 'pending':
        trial_request.status = 'approved'
        trial_request.save(update_fields=['status'])

    serializer = OrderSerializer(order)
    return APIResponse(code=0, msg='Payment confirmed', data=serializer.data)


@api_view(['POST'])
@authentication_classes([AdminTokenAuthtication])
def cancel_order(request):
    try:
        order = Order.objects.get(pk=request.GET.get('id', -1))
    except Order.DoesNotExist:
        return APIResponse(code=1, msg='Order does not exist')

    if order.status == 8:
        return APIResponse(code=1, msg='Done orders cannot be canceled')

    order.status = 7
    order.save(update_fields=['status'])
    serializer = OrderSerializer(order)
    return APIResponse(code=0, msg='Canceled', data=serializer.data)


@api_view(['POST'])
@authentication_classes([AdminTokenAuthtication])
def delete(request):
    ids = request.GET.get('ids')
    if not ids:
        return APIResponse(code=1, msg='Order ids are required')

    ids_arr = [item for item in ids.split(',') if item]
    Order.objects.filter(id__in=ids_arr).delete()
    return APIResponse(code=0, msg='Deleted')


@api_view(['POST'])
@authentication_classes([AdminTokenAuthtication])
def check_in_order(request):
    try:
        order = Order.objects.select_related('thing', 'child').get(id=request.GET.get('id'))
    except Order.DoesNotExist:
        return APIResponse(code=1, msg='Order does not exist')

    if order.status == 6:
        return APIResponse(code=1, msg='Order is already scheduled')
    if order.status != 2:
        return APIResponse(code=1, msg='Only paid orders can be scheduled')

    trial_request = TrialRequest.objects.filter(package_order=order).select_related(
        'robotics_class',
        'coding_class',
        'child',
    ).first()

    if trial_request:
        trial_things = [
            thing for thing in [
                trial_request.robotics_class,
                trial_request.coding_class,
            ]
            if thing
        ]
        conflict = selected_slot_conflict(trial_things)
        if conflict:
            return APIResponse(code=1, msg=conflict)

        for thing in trial_things:
            conflict = student_slot_conflict(
                trial_request.child,
                thing,
                exclude_order_id=order.id,
                exclude_trial_request_id=trial_request.id,
            )
            if conflict:
                return APIResponse(code=1, msg=conflict)

        for thing in trial_things:
            lesson = Lesson.objects.get_or_create(thing=thing)[0]
            lesson.try_students.add(trial_request.child)
            lesson.save()

        trial_request.status = 'scheduled'
        trial_request.save(update_fields=['status'])
        order.status = 6
        order.save(update_fields=['status'])
        serializer = OrderSerializer(order)
        return APIResponse(code=0, msg='Scheduled', data=serializer.data)

    capacity_error = _validate_normal_order_capacity(order)
    if capacity_error:
        return APIResponse(code=1, msg=capacity_error)

    order.status = 6
    order.save(update_fields=['status'])
    serializer = OrderSerializer(order)
    return APIResponse(code=0, msg='Scheduled', data=serializer.data)


@api_view(['POST'])
@authentication_classes([AdminTokenAuthtication])
def check_out_order(request):
    try:
        order = Order.objects.get(id=request.GET.get('id'))
    except Order.DoesNotExist:
        return APIResponse(code=1, msg='Order does not exist')

    order.status = 8
    order.save(update_fields=['status'])
    serializer = OrderSerializer(order)
    return APIResponse(code=0, msg='Done', data=serializer.data)
