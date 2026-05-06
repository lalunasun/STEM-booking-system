from rest_framework.decorators import api_view, authentication_classes

from CSAA import utils
from CSAA.auth.authentication import AdminTokenAuthtication
from CSAA.handler import APIResponse
from CSAA.models import Time
from CSAA.serializers import TimeSerializer


# Time列表
@api_view(['GET'])
def list_api(request):
    if request.method == 'GET':
        times = Time.objects.all()
        serializer = TimeSerializer(times, many=True)
        return APIResponse(code=0, msg='查询成功', data=serializer.data)


# 创建Time
@api_view(['POST'])
@authentication_classes([AdminTokenAuthtication])
def create(request):
    # 查询当前Time是否已经存在
    times = Time.objects.filter(time=request.data['time'])
    if len(times) > 0:
        return APIResponse(code=1, msg='该名称已存在')

    serializer = TimeSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return APIResponse(code=0, msg='创建成功', data=serializer.data)
    else:
        utils.log_error(request, '添加Time输入参数错误')

    return APIResponse(code=1, msg='创建失败')


# 修改Time
@api_view(['POST'])
@authentication_classes([AdminTokenAuthtication])
def update(request):
    try:
        pk = request.GET.get('id', -1)
        times = Time.objects.get(pk=pk)
    except Time.DoesNotExist:
        return APIResponse(code=1, msg='Time不存在')

    serializer = TimeSerializer(times, data=request.data)
    if serializer.is_valid():
        serializer.save()
        return APIResponse(code=0, msg='更新成功', data=serializer.data)
    else:
        utils.log_error(request, '修改Time输入参数错误')

    return APIResponse(code=1, msg='更新失败')


# 删除Time
@api_view(['POST'])
@authentication_classes([AdminTokenAuthtication])
def delete(request):
    try:
        ids = request.GET.get('ids')
        ids_arr = ids.split(',')
        Time.objects.filter(id__in=ids_arr).delete()
    except Time.DoesNotExist:
        return APIResponse(code=1, msg='Time不存在')

    return APIResponse(code=0, msg='删除成功')
