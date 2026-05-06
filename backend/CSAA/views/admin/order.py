import datetime
from datetime import timedelta

from rest_framework.decorators import api_view, authentication_classes

from CSAA import utils
from CSAA.auth.authentication import AdminTokenAuthtication
from CSAA.handler import APIResponse
from CSAA.models import Order, Thing
from CSAA.serializers import OrderSerializer, ThingSerializer


# 订单信息列表
@api_view(['GET'])
def list_api(request):
    if request.method == 'GET':
        orders = Order.objects.all().order_by('-order_time')
        serializer = OrderSerializer(orders, many=True)
        return APIResponse(code=0, msg='查询成功', data=serializer.data)
        serializer = OrderSerializer(orders, many=True)
        return APIResponse(code=0, msg='查询成功', data=serializer.data)


# 创建订单
@api_view(['POST'])
@authentication_classes([AdminTokenAuthtication])  # 管理员身份验证
def create(request):
    data = request.data.copy()

    if data['user'] is None or data['thing'] is None or data['count'] is None\
            or data['expect_time'] is None or data['return_time'] is None:
        return APIResponse(code=1, msg='创建订单参数错误')

    thing = Thing.objects.get(pk=data['thing'])
    count = data['count']
    #if thing.repertory < int(count):
        #return APIResponse(code=1, msg='课程数量不足')

    if thing.status == 0:
        return APIResponse(code=1,msg='课程已下架')

    expect_time = data.get('expect_time')
    return_time = data.get('return_time')
    # 计算课时数
    time_range = [expect_time + timedelta(days=i) for i in range((return_time - expect_time).days + 1)]
    # 查询每天该类型课程的剩余数量
    for day in time_range:
        existing_orders = Order.objects.filter(thing=thing,
                                               status__in=['1', '2', '6', '8'],
                                               expect_time__lte=day, return_time__gte=day)
        room_count = Thing.objects.get(pk=thing).repertory
        total_room_count = room_count - existing_orders.count()
        if count > total_room_count:
            return APIResponse(code=1, msg=f'选择的入住时间段内该类型课程数量不足，剩余课程数量为{total_room_count}')


    # 处理时间
    create_time = datetime.datetime.now()
    data['create_time'] = create_time
    data['order_number'] = str(utils.get_timestamp())  # 通过当前的时间戳生成订单号
    #data['status'] = '1'
    serializer = OrderSerializer(data=data)
    if serializer.is_valid():
        serializer.save()


        # 空闲课程数量减少
        thing.repertory -= int(count)
        #if thing.repertory == 0:
            #thing.status = 1
        thing.save()

        print(serializer)
        return APIResponse(code=0, msg='创建成功', data=serializer.data)
    else:
        print(serializer.errors)
        return APIResponse(code=1, msg='创建失败')


# 修改订单
@api_view(['POST'])
@authentication_classes([AdminTokenAuthtication])
def update(request):
    try:
        pk = request.GET.get('id', -1)
        order = Order.objects.get(pk=pk)
    except Order.DoesNotExist:
        return APIResponse(code=1, msg='订单不存在')

    serializer = OrderSerializer(order, data=request.data)
    if serializer.is_valid():
        serializer.save()
        return APIResponse(code=0, msg='更新成功', data=serializer.data)
    else:
        print(serializer.errors)
        return APIResponse(code=1, msg='更新失败')


# 取消订单
@api_view(['POST'])
@authentication_classes([AdminTokenAuthtication])
def cancel_order(request):
    try:
        pk = request.GET.get('id', -1)
        order = Order.objects.get(pk=pk)
    except Order.DoesNotExist:
        return APIResponse(code=1, msg='订单不存在')

    data = {
        'status': 7  # 修改状态为取消
    }
    serializer = OrderSerializer(order, data=data)
    if serializer.is_valid():
        serializer.save()


        # 空闲课程数量增加
        thing = order.thing
        count = order.count
        #if thing.repertory == 0:
            #thing.status = 0
        repertory = int(thing.repertory)
        repertory += int(count)
        thing.repertory = str(repertory)
        thing.save()


        return APIResponse(code=0, msg='取消成功', data=serializer.data)
    else:
        print(serializer.errors)
        return APIResponse(code=1, msg='更新失败')


@api_view(['POST'])
@authentication_classes([AdminTokenAuthtication])
def delete(request):
    try:
        ids = request.GET.get('ids')
        if not ids:
            return APIResponse(code=1, msg='参数错误')

        ids_arr = ids.split(',')
        orders = Order.objects.filter(id__in=ids_arr)

        # 检查订单状态
        for order in orders:


            # 归还课程数量
            thing = order.thing
            if order.status not in ['7', '8']:  # 7取消 8完成
                repertory = int(thing.repertory)
                repertory += int(order.count)
                thing.repertory = str(repertory)
                thing.save()
                order.delete()



        return APIResponse(code=0, msg='删除成功')

    except Exception as e:
        return APIResponse(code=1, msg=f'删除失败:{str(e)}')


# 完成订单
#@api_view(['POST'])
#@authentication_classes([AdminTokenAuthtication])
#def ok_order(request):
    #try:
        #id = request.GET.get('id')
        #order = Order.objects.get(id=id)
        #thing = Thing.objects.get(id=order.thing_id)
    #except Order.DoesNotExist:
        #return APIResponse(code=1, msg='订单不存在')
    #data = {
        #'status': 0  # 修改状态为完成
    #}
    #data1 = {
        #'status': 0  # 修改课程状态为空闲
    #}
    #serializer = OrderSerializer(order, data=data)
    #serializer1 = ThingSerializer(thing, data=data1)
    #if serializer.is_valid() and serializer1.is_valid():
        #serializer.save()
        #serializer1.save()

        #return APIResponse(code=0, msg='操作成功', data=serializer.data)
    #else:
        #print(serializer.errors, serializer1.errors)
        #return APIResponse(code=1, msg='操作失败')

@api_view(['POST'])
@authentication_classes([AdminTokenAuthtication])
def check_in_order(request):
    try:
        id = request.GET.get('id')
        order = Order.objects.get(id=id)
        thing = Thing.objects.get(id=order.thing_id)
    except Order.DoesNotExist:
        return APIResponse(code=1, msg='订单不存在')

    if order.status == 6:  # 如果订单已经入住
        return APIResponse(code=1, msg='已入住')

    data = {
        'status': 6  # 修改状态为入住
    }
    #data1 = {
        #'status': 1  # 修改课程状态为无库存
    #}
    serializer = OrderSerializer(order, data=data)
    #serializer1 = ThingSerializer(thing, data=data1)
    if serializer.is_valid():  # and serializer1.is_valid():
        serializer.save()
        #serializer1.save()
        return APIResponse(code=0, msg='更新成功', data=serializer.data)
    else:
        print(serializer.errors)  #, serializer1.errors)
        return APIResponse(code=1, msg='更新失败')

@api_view(['POST'])
@authentication_classes([AdminTokenAuthtication])
def check_out_order(request):
    try:
        id = request.GET.get('id')
        order = Order.objects.get(id=id)
    except Order.DoesNotExist:
        return APIResponse(code=1, msg='订单不存在')
    data = {
        'status': 8  # 修改订单状态为完成
    }
    serializer = OrderSerializer(order, data=data)
    if serializer.is_valid():
        serializer.save()
        # 订单结束后，空闲课程数量增加
        thing = order.thing  # 获取订单的课程类型
        #if thing.repertory == 0:
            #thing.status = 0
        repertory = int(thing.repertory)
        repertory += order.count  # 增加空闲课程数量
        thing.repertory = str(repertory)
        thing.save()

        return APIResponse(code=0, msg='退房成功', data=serializer.data)
    else:
        return APIResponse(code=1, msg='退房失败')