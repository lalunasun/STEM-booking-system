from rest_framework.decorators import api_view, authentication_classes

from CSAA import utils
from CSAA.auth.authentication import AdminTokenAuthtication, TokenAuthtication
from CSAA.handler import APIResponse
from CSAA.models import Child, User
from CSAA.serializers import ChildSerializer


# child列表
@api_view(['GET'])
def list_api(request):
    if request.method == 'GET':
        user = User.objects.get(id=request.GET.get('parent', -1))
        childs = Child.objects.filter(parent=user)
        serializer = ChildSerializer(childs, many=True)
        return APIResponse(code=0, msg='查询成功', data=serializer.data)


# 创建child
@api_view(['POST'])
@authentication_classes([TokenAuthtication])
def create(request):
    data = request.data.copy()
    print(data)
    serializer = ChildSerializer(data=data)
    print(serializer)
    if serializer.is_valid():
        serializer.save()
        return APIResponse(code=0, msg='创建成功', data=serializer.data)
    else:
        utils.log_error(request, '添加child输入参数错误')

    return APIResponse(msg='创建失败', status=500)


# 修改child
@api_view(['POST'])
@authentication_classes([AdminTokenAuthtication])
def update(request):
    try:
        pk = request.GET.get('id', -1)
        childs = Child.objects.get(pk=pk)
    except Child.DoesNotExist:
        return APIResponse(code=1, msg='child不存在')

    serializer = ChildSerializer(childs, data=request.data)
    if serializer.is_valid():
        serializer.save()
        return APIResponse(code=0, msg='更新成功', data=serializer.data)
    else:
        utils.log_error(request, '修改child输入参数错误')

    return APIResponse(code=1, msg='更新失败')


# 删除child
@api_view(['POST'])
@authentication_classes([AdminTokenAuthtication])
def delete(request):
    try:
        ids = request.GET.get('ids')
        ids_arr = ids.split(',')
        Child.objects.filter(id__in=ids_arr).delete()
    except Child.DoesNotExist:
        return APIResponse(code=1, msg='child不存在')

    return APIResponse(code=0, msg='删除成功')
