from django.db.models import Q
from rest_framework.decorators import api_view, authentication_classes

from CSAA import utils
from CSAA.auth.authentication import AdminTokenAuthtication
from CSAA.handler import APIResponse
from CSAA.models import Child
from CSAA.serializers import AdminStudentSerializer


@api_view(['GET'])
def list_api(request):
    keyword = request.GET.get('keyword', '')
    students = Child.objects.select_related('parent').all().order_by('parent__username', 'name')

    if keyword:
        students = students.filter(
            Q(name__contains=keyword)
            | Q(parent__username__contains=keyword)
            | Q(parent__nickname__contains=keyword)
            | Q(parent__mobile__contains=keyword)
        )

    serializer = AdminStudentSerializer(students, many=True)
    return APIResponse(code=0, msg='查询成功', data=serializer.data)


@api_view(['POST'])
@authentication_classes([AdminTokenAuthtication])
def create(request):
    serializer = AdminStudentSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return APIResponse(code=0, msg='创建成功', data=serializer.data)

    utils.log_error(request, '添加student输入参数错误')
    return APIResponse(code=1, msg='创建失败')


@api_view(['POST'])
@authentication_classes([AdminTokenAuthtication])
def update(request):
    try:
        pk = request.GET.get('id', -1)
        student = Child.objects.get(pk=pk)
    except Child.DoesNotExist:
        return APIResponse(code=1, msg='Student不存在')

    serializer = AdminStudentSerializer(student, data=request.data)
    if serializer.is_valid():
        serializer.save()
        return APIResponse(code=0, msg='更新成功', data=serializer.data)

    utils.log_error(request, '修改student输入参数错误')
    return APIResponse(code=1, msg='更新失败')


@api_view(['POST'])
@authentication_classes([AdminTokenAuthtication])
def delete(request):
    try:
        ids = request.GET.get('ids')
        ids_arr = ids.split(',')
        Child.objects.filter(id__in=ids_arr).delete()
    except Exception:
        return APIResponse(code=1, msg='Student不存在')

    return APIResponse(code=0, msg='删除成功')
