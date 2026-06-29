import datetime
from decimal import Decimal, InvalidOperation
from datetime import timedelta

from rest_framework.decorators import api_view, authentication_classes

from CSAA import utils

from CSAA.auth.authentication import TokenAuthtication
from CSAA.course_conflicts import student_slot_conflict
from CSAA.handler import APIResponse
from CSAA.models import Order, Thing, User, Lesson, Child
from CSAA.serializers import OrderSerializer, ThingSerializer


def _is_trial_course(thing):
    title = ''
    if thing.classification and thing.classification.title:
        title = thing.classification.title
    return title.strip().lower() == 'trial'


def _trial_amount(thing):
    try:
        return str(Decimal(str(thing.price or '0')) * Decimal('2'))
    except (InvalidOperation, TypeError, ValueError):
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
    conflict = student_slot_conflict(child, thing)
    if conflict:
        return APIResponse(code=1, msg=conflict)

    if _is_trial_course(thing):
        data['num'] = '2'
        amount = _trial_amount(thing)
        if amount is not None:
            data['amount'] = amount
    create_time = datetime.datetime.now()
    data['create_time'] = create_time
    data['order_number'] = str(utils.get_timestamp())  # 用当前的时间戳生成订单号
    data['status'] = '1'
    data['receiver_phone'] = user.mobile


    data['expect_time'] = expect_time  # 设置开课时间
    data['return_time'] = return_time  # 设置结课时间
    # 定义日期字符串的格式

    same_room_thing = Thing.objects.filter(tag=thing.tag, day=thing.day, time=thing.time)
    counts = 0
    for item in same_room_thing:
        order = Order.objects.filter(thing=item,
                                     status__in=['1', '2', '6', '8'])
        counts = counts + order.count()
    room_count = thing.tag.seat
    room_count = int(room_count)
    total_room_count = room_count - counts
    if total_room_count == 0:
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
    return APIResponse(code=1, msg='Payment is confirmed by the administrator')
