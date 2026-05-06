from rest_framework.decorators import api_view, authentication_classes

from CSAA import utils
from CSAA.auth.authentication import AdminTokenAuthtication
from CSAA.handler import APIResponse
from CSAA.models import Classification, Thing, Tag
from CSAA.serializers import ThingSerializer, UpdateThingSerializer

from django.db.models import Case, When, IntegerField
day_order = {
    'Mon': 1,
    'Tue': 2,
    'Wed': 3,
    'Thu': 4,
    'Fri': 5,
    'Sat': 6,
    'Sun': 7,
}


# 查询课程数据
@api_view(['GET'])  # 装饰器，只接受get请求
def list_api(request):
    if request.method == 'GET':  # 可以不用判断请求方式
        keyword = request.GET.get("keyword", None)  # 关键词
        c = request.GET.get("c", None)  # 分类
        tag = request.GET.get("tag", None)  # Room
        # 通过关键词查询
        if keyword:
            things = Thing.objects.filter(title__contains=keyword).order_by('-create_time')
        # 通过分类查询
        elif c:
            classification = Classification.objects.get(pk=c)
            things = classification.classification_thing.all()  # 该分类下的所有课程
        # 通过Room查询
        elif tag:
            tag = Tag.objects.get(id=tag)
            # print(tag)
            things = tag.thing_set.all()
        else:
            things = Thing.objects.annotate(
                day_order=Case(
                    *[When(day=day, then=order) for day, order in day_order.items()],
                    output_field=IntegerField(),
                )
            ).order_by('day_order', 'time__time')

        serializer = ThingSerializer(things, many=True)
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


# 创建课程
@api_view(['POST'])  # 直接受post请求
@authentication_classes([AdminTokenAuthtication])  # 管理员身份验证
def create(request):
    serializer = ThingSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return APIResponse(code=0, msg='创建成功', data=serializer.data)
    else:
        print(serializer.errors)
        utils.log_error(request, '输入课程参数错误')
    return APIResponse(code=1, msg='创建失败')


# 修改课程
@api_view(['POST'])
@authentication_classes([AdminTokenAuthtication])
def update(request):
    try:
        pk = request.GET.get('id', -1)
        thing = Thing.objects.get(pk=pk)
    except Thing.DoesNotExist:
        return APIResponse(code=1, msg='课程不存在')

    serializer = UpdateThingSerializer(thing, data=request.data)
    if serializer.is_valid():
        serializer.save()
        return APIResponse(code=0, msg='查询成功', data=serializer.data)
    else:
        # print(serializer.errors)
        utils.log_error(request, '输入课程修改参数错误')

    return APIResponse(code=1, msg='更新失败')


# 删除课程
@api_view(['POST'])
@authentication_classes([AdminTokenAuthtication])
def delete(request):
    try:
        ids = request.GET.get('ids')
        ids_arr = ids.split(',')
        Thing.objects.filter(id__in=ids_arr).delete()
    except Thing.DoesNotExist:
        return APIResponse(code=1, msg='课程不存在')
    return APIResponse(code=0, msg='删除成功')
