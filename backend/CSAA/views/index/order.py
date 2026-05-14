import datetime
import json
from datetime import timedelta

from django.db import transaction
from rest_framework.decorators import api_view, authentication_classes

from CSAA import utils

from CSAA.auth.authentication import TokenAuthtication
from CSAA.handler import APIResponse
from CSAA.models import Order, Thing, User, Lesson, Child, Term
from CSAA.serializers import OrderSerializer, ThingSerializer


ACTIVE_ORDER_STATUSES = [1, 2, 6]
DAY_OF_WEEK = {
    'Mon': 0,
    'Tue': 1,
    'Wed': 2,
    'Thu': 3,
    'Fri': 4,
    'Sat': 5,
    'Sun': 6,
}


def _active_room_time_order_count(thing):
    same_room_things = Thing.objects.filter(tag=thing.tag, day=thing.day, time=thing.time)
    return Order.objects.filter(
        thing__in=same_room_things,
        child__isnull=False,
        status__in=ACTIVE_ORDER_STATUSES,
    ).count()


def _available_seats(thing):
    if not thing.tag or thing.tag.seat is None:
        return None
    return int(thing.tag.seat) - _active_room_time_order_count(thing)


def _first_trial_lesson_date(thing, term):
    if not thing.day or thing.day not in DAY_OF_WEEK:
        return None

    today = datetime.date.today()
    start = term.expect_time.date() if term.expect_time else today
    end = term.return_time.date() if term.return_time else start
    cursor = max(start, today)
    target_weekday = DAY_OF_WEEK[thing.day]

    while cursor <= end:
        if cursor.weekday() == target_weekday:
            return cursor
        cursor += datetime.timedelta(days=1)
    return None


# 获取订单列表
@api_view(['GET'])
def list_api(request):
    if request.method == 'GET':
        userId = request.GET.get('userId', -1)
        orderStatus = request.GET.get('orderStatus', '')  # 订单状态
        orders = Order.objects.all().filter(user=userId).filter(status__contains=orderStatus).order_by('-order_time')

        serializer = OrderSerializer(orders, many=True)
        return APIResponse(code=0, msg='查询成功', data=serializer.data)


# 创建订单
@api_view(['POST'])
@authentication_classes([TokenAuthtication])  # 用户token验证
def create(request):
    data = request.data.copy()
    # print(data['user'])
    user = User.objects.get(id=data['user'])

    count = data.get('count')  # 课时数
    expect_time = data.get('expect_time')  # 开课时间
    return_time = data.get('return_time')  # 结课时间
    data['status'] = '1'  # 设置订单初始状态为待支付状态

    # print(user.mobile)
    if data['user'] is None or data['thing'] is None or \
            data['count'] is None or data['expect_time'] is None or data['return_time'] is None:
        return APIResponse(code=1, msg='创建订单参数错误')
    thing = Thing.objects.get(pk=data['thing'])
    child = Child.objects.get(pk=data['child'])
    create_time = datetime.datetime.now()
    data['create_time'] = create_time
    data['order_number'] = str(utils.get_timestamp())  # 用当前的时间戳生成订单号
    data['status'] = '1'
    data['receiver_phone'] = user.mobile


    data['expect_time'] = expect_time  # 设置开课时间
    data['return_time'] = return_time  # 设置结课时间
    # 定义日期字符串的格式

    total_room_count = _available_seats(thing)
    if total_room_count is not None and total_room_count <= 0:
        return APIResponse(code=1, msg=f'Class in this period is FULL')

    serializer = OrderSerializer(data=data)
  #  print(serializer)
    if serializer.is_valid():
        lesson = Lesson.objects.get_or_create(thing=thing)[0]
        lesson.students.add(child)
        lesson.students_num += 1
        lesson.save()
        serializer.save()

        print(lesson.students)
        return APIResponse(code=0, msg='创建成功', data=serializer.data)
    else:
        print(serializer.errors)
        return APIResponse(code=1, msg='创建失败')


# 取消订单
@api_view(['POST'])
@authentication_classes([TokenAuthtication])
def create_trial(request):
    data = request.data.copy()
    user_id = data.get('user')
    child_id = data.get('child')
    term_id = data.get('term')
    thing_ids_value = data.get('thing_ids')

    if not user_id or not child_id or not term_id or not thing_ids_value:
        return APIResponse(code=1, msg='Trial order parameters are missing')

    try:
        thing_ids = json.loads(thing_ids_value) if isinstance(thing_ids_value, str) else list(thing_ids_value)
        thing_ids = [int(thing_id) for thing_id in thing_ids if thing_id]
    except (TypeError, ValueError):
        return APIResponse(code=1, msg='Trial class selection is invalid')

    if len(thing_ids) < 2:
        return APIResponse(code=1, msg='Please select Robotics and Coding trial classes')

    try:
        user = User.objects.get(id=user_id)
        child = Child.objects.get(pk=child_id)
        term = Term.objects.get(pk=term_id)
        things = list(Thing.objects.filter(id__in=thing_ids).select_related('tag', 'time', 'classification'))
    except (User.DoesNotExist, Child.DoesNotExist, Term.DoesNotExist):
        return APIResponse(code=1, msg='Trial order references invalid data')

    if len(things) != len(thing_ids):
        return APIResponse(code=1, msg='One or more selected trial classes do not exist')

    for thing in things:
        if str(thing.status) == '1':
            return APIResponse(code=1, msg=f'{thing.title} is unavailable')
        available_seats = _available_seats(thing)
        if available_seats is not None and available_seats <= 0:
            time_label = thing.time.time if thing.time else ''
            return APIResponse(code=1, msg=f'{thing.title} {thing.day} {time_label} is FULL')
        if not _first_trial_lesson_date(thing, term):
            return APIResponse(code=1, msg=f'{thing.title} has no available trial date in this term')

    created_orders = []
    with transaction.atomic():
        for index, thing in enumerate(things):
            lesson_date = _first_trial_lesson_date(thing, term)
            lesson_datetime = datetime.datetime.combine(lesson_date, datetime.time.min)
            order_data = {
                'order_number': str(utils.get_timestamp() + index),
                'user': user.id,
                'thing': thing.id,
                'count': 1,
                'num': 1,
                'child': child.id,
                'expect_time': lesson_datetime,
                'return_time': lesson_datetime,
                'term': term.id,
                'amount': str(thing.price or 0),
                'status': 1,
                'receiver_phone': user.mobile,
                'remark': f'Trial package - {thing.classification.title if thing.classification else thing.title}',
            }
            serializer = OrderSerializer(data=order_data)
            if not serializer.is_valid():
                return APIResponse(code=1, msg='Create trial order failed')
            created_orders.append(serializer.save())

    serializer = OrderSerializer(created_orders, many=True)
    return APIResponse(code=0, msg='Trial order created', data=serializer.data)


@api_view(['POST'])
@authentication_classes([TokenAuthtication])
def cancel_order(request):
    print("取消订单")
    try:
        pk = request.GET.get('id', -1)
        order = Order.objects.get(pk=pk)
        # thing = Thing.objects.get(id=order.thing_id)
    except Order.DoesNotExist:
        return APIResponse(code=1, msg='订单不存在')
    data = {
        'status': 7
    }
    serializer = OrderSerializer(order, data=data)
    if serializer.is_valid():
        serializer.save()
        return APIResponse(code=0, msg='取消成功', data=serializer.data)
    else:
        print(serializer.errors)
        return APIResponse(code=1, msg='更新失败')


# 支付订单
@api_view(['POST'])
@authentication_classes([TokenAuthtication])
def pay_order(request):
    print("支付订单")
    try:
        # pk = request.GET.get('id', -1)
        pk = request.GET.get('id', -1)
        order = Order.objects.get(pk=pk)
        thing = Thing.objects.get(id=order.thing_id)
    except Order.DoesNotExist or Thing.DoesNotExist:
        return APIResponse(code=1, msg='订单不存在')
    data = {
        'status': 2
    }
    # data1 = {
    # 'status': 1
    # }
    serializer = OrderSerializer(order, data=data)
    # serializer1 = ThingSerializer(thing, data=data1)

    # if serializer.is_valid() and serializer1.is_valid():
    if serializer.is_valid():
        serializer.save()
        # serializer1.save()
        return APIResponse(code=0, msg='支付成功', data=serializer.data)
    else:
        print(serializer.errors)  # ,serializer1.errors)
        return APIResponse(code=1, msg='支付失败')
