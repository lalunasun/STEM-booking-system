from rest_framework.decorators import api_view, authentication_classes

from CSAA.auth.authentication import AdminTokenAuthtication
from CSAA.handler import APIResponse
from CSAA.models import Ad
from CSAA.serializers import AdSerializer


# 获取广告信息
@api_view(['GET'])  # 请求方式装饰器，只接受get请求
def list_api(request):
    if request.method == 'GET':
        ads = Ad.objects.all().order_by('-create_time')
        serializer = AdSerializer(ads, many=True)
        return APIResponse(code=0, msg='查询成功', data=serializer.data)


# 创建广告
@api_view(['POST'])  # 只接受post请求
@authentication_classes([AdminTokenAuthtication])  # 管理员身份验证，只能管理员才能操作
def create(request):
    serializer = AdSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return APIResponse(code=0, msg='创建成功', data=serializer.data)

    return APIResponse(code=1, msg='创建失败')


# 修改广告信息
@api_view(['POST'])
@authentication_classes([AdminTokenAuthtication])  # 管理员身份验证，只能管理员才能操作
def update(request):
    # 查询广告是否存在
    try:
        pk = request.GET.get('id', -1)
        ad = Ad.objects.get(pk=pk)
    except Ad.DoesNotExist:
        return APIResponse(code=1, msg='广告不存在')
    # 修改广告
    serializer = AdSerializer(ad, data=request.data)
    if serializer.is_valid():
        serializer.save()
        return APIResponse(code=0, msg='更新成功', data=serializer.data)
    else:
        print(serializer.errors)

    return APIResponse(code=1, msg='更新失败')


# 删除广告
@api_view(['POST'])
@authentication_classes([AdminTokenAuthtication])
def delete(request):
    # 批量删除时需要分割ids在删除
    try:
        ids = request.GET.get('ids')
        ids_arr = ids.split(',')
        Ad.objects.filter(id__in=ids_arr).delete()
    except Ad.DoesNotExist:
        return APIResponse(code=1, msg='广告不存在')

    return APIResponse(code=0, msg='删除成功')
