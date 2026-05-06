from rest_framework.decorators import api_view

from CSAA import utils
from CSAA.handler import APIResponse
from CSAA.models import Thing, Tag, User, Order
from CSAA.serializers import ThingSerializer, ListThingSerializer, DetailThingSerializer


# 首页课程数据
@api_view(['GET'])
def list_api(request):
    if request.method == 'GET':
        # print("首页获取数据")
        all_thing = Thing.objects.all()
        for thing in all_thing:
            same_room_thing = Thing.objects.filter(tag=thing.tag, day=thing.day, time=thing.time)
            counts = 0
            for item in same_room_thing:
                order = Order.objects.filter(thing=item,
                                                   status__in=['1', '2', '6', '8'])
                counts = counts + order.count()
            room_count = thing.tag.seat
            room_count = int(room_count)
            total_room_count = room_count - counts
            if thing.status == '1' and total_room_count > 0:
                thing.status = '0'
                thing.save()
            elif thing.status == '0' and total_room_count == 0:
                thing.status = '1'
                thing.save()


        keyword = request.GET.get("keyword", None)  # 关键词
        c = request.GET.get("c", None)  # 分类
        tag = request.GET.get("tag", None)  # 标签
        sort = request.GET.get("sort", 'recent')  # 排序

        # 排序方式
        order = '-create_time'
        if sort == 'recent':
            order = '-create_time'
        elif sort == 'hot' or sort == 'recommend':
            order = '-pv'

        if keyword:
            things = Thing.objects.filter(title__contains=keyword).order_by(order)

        elif c and int(c) > -1:
            ids = [c]
            things = Thing.objects.filter(classification_id__in=ids).order_by(order)

        elif tag:
            tag = Tag.objects.get(id=tag)
            # print(tag)
            things = tag.thing_set.all().order_by(order)

        else:
            # 延迟加载
            things = Thing.objects.all().defer('wish').order_by(order)


        serializer = ListThingSerializer(things, many=True)
        return APIResponse(code=0, msg='查询成功', data=serializer.data)


# 课程详情
@api_view(['GET'])
def detail(request):
    try:
        pk = request.GET.get('id', -1)
        thing = Thing.objects.get(pk=pk)
    except Thing.DoesNotExist:
        utils.log_error(request, '课程不存在')
        return APIResponse(code=1, msg='课程不存在')

    if request.method == 'GET':
        serializer = ThingSerializer(thing)
        return APIResponse(code=0, msg='查询成功', data=serializer.data)


# 增加想要
@api_view(['POST'])
def increaseWishCount(request):
    try:
        pk = request.GET.get('id', -1)
        thing = Thing.objects.get(pk=pk)
        # wish_count加1
        thing.wish_count = thing.wish_count + 1
        thing.save()
    except Thing.DoesNotExist:
        utils.log_error(request, '课程不存在')
        return APIResponse(code=1, msg='课程不存在')

    serializer = ThingSerializer(thing)
    return APIResponse(code=0, msg='操作成功', data=serializer.data)


# 增加评论数量
@api_view(['POST'])
def increaseRecommendCount(request):
    try:
        pk = request.GET.get('id', -1)
        thing = Thing.objects.get(pk=pk)
        thing.recommend_count = thing.recommend_count + 1
        thing.save()
    except Thing.DoesNotExist:
        utils.log_error(request, '课程不存在')
        return APIResponse(code=1, msg='课程不存在')

    serializer = ThingSerializer(thing)
    return APIResponse(code=0, msg='操作成功', data=serializer.data)


# 用户增加想要
@api_view(['POST'])  # 只接受post请求
def addWishUser(request):
    try:
        username = request.GET.get('username', None)  # 用户名
        thingId = request.GET.get('thingId', None)  # 课程id

        if username and thingId:
            user = User.objects.get(username=username)
            thing = Thing.objects.get(pk=thingId)

            # 未添加则添加想要
            if user not in thing.wish.all():
                thing.wish.add(user)
                thing.wish_count += 1
                thing.save()

    except Thing.DoesNotExist:
        utils.log_error(request, '添加想要操作失败')
        return APIResponse(code=1, msg='添加想要操作失败')

    serializer = ThingSerializer(thing)
    return APIResponse(code=0, msg='操作成功', data=serializer.data)


# 移除想要
@api_view(['POST'])
def removeWishUser(request):
    try:
        username = request.GET.get('username', None)
        thingId = request.GET.get('thingId', None)

        if username and thingId:
            user = User.objects.get(username=username)
            thing = Thing.objects.get(pk=thingId)

            # 有则移除
            if user in thing.wish.all():
                thing.wish.remove(user)
                thing.wish_count -= 1
                thing.save()

    except Thing.DoesNotExist:
        utils.log_error(request, '移除想要操作失败')
        return APIResponse(code=1, msg='移除想要操作失败')

    return APIResponse(code=0, msg='操作成功')


# 获取想要课程列表
@api_view(['GET'])
def getWishThingList(request):
    try:
        username = request.GET.get('username', None)
        if username:
            user = User.objects.get(username=username)
            things = user.wish_things.all()
            serializer = ListThingSerializer(things, many=True)
            return APIResponse(code=0, msg='操作成功', data=serializer.data)
        else:
            return APIResponse(code=1, msg='username不能为空')

    except Exception as e:
        utils.log_error(request, '操作失败' + str(e))
        return APIResponse(code=1, msg='获取心愿单失败')


# 添加收藏
@api_view(['POST'])
def addCollectUser(request):
    try:
        username = request.GET.get('username', None)
        thingId = request.GET.get('thingId', None)

        if username and thingId:
            user = User.objects.get(username=username)
            thing = Thing.objects.get(pk=thingId)

            # 未收藏则收藏，且收藏数量+1
            if user not in thing.collect.all():
                thing.collect.add(user)
                thing.collect_count += 1
                thing.save()

    except Thing.DoesNotExist:
        utils.log_error(request, '用户添加收藏操作失败')
        return APIResponse(code=1, msg='用户添加收藏操作失败')

    serializer = DetailThingSerializer(thing)
    return APIResponse(code=0, msg='操作成功', data=serializer.data)


# 移除收藏
@api_view(['POST'])
def removeCollectUser(request):
    try:
        username = request.GET.get('username', None)
        thingId = request.GET.get('thingId', None)

        if username and thingId:
            user = User.objects.get(username=username)
            thing = Thing.objects.get(pk=thingId)
            # 有则移除
            if user in thing.collect.all():
                thing.collect.remove(user)
                thing.collect_count -= 1
                thing.save()

    except Thing.DoesNotExist:
        utils.log_error(request, '用户移除收藏操作失败')
        return APIResponse(code=1, msg='用户移除收藏操作失败')

    return APIResponse(code=0, msg='操作成功')


# 获取用户收藏列表
@api_view(['GET'])
def getCollectThingList(request):
    try:
        username = request.GET.get('username', None)
        if username:
            user = User.objects.get(username=username)
            things = user.collect_things.all()
            serializer = ListThingSerializer(things, many=True)
            return APIResponse(code=0, msg='操作成功', data=serializer.data)
        else:
            return APIResponse(code=1, msg='username不能为空')

    except Exception as e:
        utils.log_error(request, '操作失败' + str(e))
        return APIResponse(code=1, msg='获取收藏失败')
