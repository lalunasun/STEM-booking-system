from rest_framework.decorators import api_view, authentication_classes

from CSAA import utils
from CSAA.auth.authentication import AdminTokenAuthtication
from CSAA.handler import APIResponse
from CSAA.models import Classification, Thing, Tag, Lesson
from CSAA.serializers import ThingSerializer, UpdateThingSerializer, LessonSerializer, LessonDetailSerializer


# 查询课程数据
@api_view(['GET'])  # 装饰器，只接受get请求
def list_api(request):
    if request.method == 'GET':  # 可以不用判断请求方式

        lessons = Lesson.objects.all()

        serializer = LessonSerializer(lessons, many=True)
        return APIResponse(code=0, msg='查询成功', data=serializer.data)


# 课程详情
@api_view(['GET'])
def detail(request):
    try:
        pk = request.GET.get('id', -1)
        thing = Thing.objects.get(pk=pk)
        print(pk)
        print(thing)
        lesson = Lesson.objects.get(thing=thing)
    except Lesson.DoesNotExist:
        utils.log_error(request, '课程不存在')
        return APIResponse(code=1, msg='课程不存在')

    if request.method == 'GET':
        serializer = LessonDetailSerializer(lesson)
        return APIResponse(code=0, msg='查询成功', data=serializer.data)


# 创建课程
@api_view(['POST'])  # 直接受post请求
@authentication_classes([AdminTokenAuthtication])  # 管理员身份验证
def create(request):
    serializer = LessonSerializer(data=request.data)
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
        lesson = Lesson.objects.get(pk=pk)
    except Lesson.DoesNotExist:
        return APIResponse(code=1, msg='课程不存在')

    serializer = UpdateLessonSerializer(lesson, data=request.data)
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
        Lesson.objects.filter(id__in=ids_arr).delete()
    except Lesson.DoesNotExist:
        return APIResponse(code=1, msg='课程不存在')
    return APIResponse(code=0, msg='删除成功')
