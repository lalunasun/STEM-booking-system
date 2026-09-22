from rest_framework.decorators import api_view, authentication_classes

from CSAA import utils
from CSAA.auth.authentication import AdminTokenAuthtication
from CSAA.handler import APIResponse
from CSAA.models import Classification, Course, Thing, Tag
from CSAA.room_permissions import protected_class_instances
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
        thing = serializer.save()
        if thing.title:
            Course.objects.get_or_create(title=str(thing.title).strip())
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
        thing = serializer.save()
        if thing.title:
            Course.objects.get_or_create(title=str(thing.title).strip())
        return APIResponse(code=0, msg='查询成功', data=serializer.data)
    else:
        # print(serializer.errors)
        utils.log_error(request, '输入课程修改参数错误')

    return APIResponse(code=1, msg='更新失败')


# 删除课程
@api_view(['POST'])
@authentication_classes([AdminTokenAuthtication])
def delete(request):
    ids = request.GET.get('ids', '')
    ids_arr = [value for value in ids.split(',') if value]
    try:
        requested_ids = {int(value) for value in ids_arr}
    except (TypeError, ValueError):
        return APIResponse(code=1, msg='Invalid class instance selection')
    things = list(Thing.objects.filter(id__in=requested_ids).select_related('tag', 'time'))
    if not things or len(things) != len(requested_ids):
        return APIResponse(code=1, msg='Class instance not found')

    protected = protected_class_instances(things)
    if protected:
        labels = []
        for thing in protected[:5]:
            room = thing.tag.title if thing.tag else 'No room'
            time = thing.time.time if thing.time else 'No time'
            labels.append(f'{room} {thing.day or "No day"} {time} {thing.title}')
        suffix = '...' if len(protected) > 5 else ''
        return APIResponse(
            code=1,
            msg=(
                'Cannot delete current class slots allowed by Room course permissions. '
                'Set the class to Unavailable or update the room permissions first: '
                + '; '.join(labels) + suffix
            ),
        )

    Thing.objects.filter(id__in=[thing.id for thing in things]).delete()
    return APIResponse(code=0, msg='删除成功')
