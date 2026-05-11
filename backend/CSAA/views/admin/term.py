from rest_framework.decorators import api_view, authentication_classes

from CSAA import utils
from CSAA.auth.authentication import AdminTokenAuthtication
from CSAA.handler import APIResponse
from CSAA.models import Term
from CSAA.serializers import TermSerializer


def normalize_term_dates(data):
    normalized = data.copy()
    expect_time = normalized.get('expect_time')
    return_time = normalized.get('return_time')

    if expect_time and 'T' not in expect_time:
        normalized['expect_time'] = expect_time + 'T00:00:00'

    if return_time and 'T' not in return_time:
        normalized['return_time'] = return_time + 'T23:59:59'

    return normalized


# term列表
@api_view(['GET'])
def list_api(request):
    if request.method == 'GET':
        terms = Term.objects.all()
        serializer = TermSerializer(terms, many=True)
        return APIResponse(code=0, msg='查询成功', data=serializer.data)


# 创建term
@api_view(['POST'])
@authentication_classes([AdminTokenAuthtication])
def create(request):
    # 查询当前term是否已经存在
    terms = Term.objects.filter(title=request.data['title'])
    if len(terms) > 0:
        return APIResponse(code=1, msg='该名称已存在')
    data = normalize_term_dates(request.data)
    serializer = TermSerializer(data=data)
    print(serializer)
    if serializer.is_valid():
        serializer.save()
        return APIResponse(code=0, msg='创建成功', data=serializer.data)
    else:
        utils.log_error(request, '添加term输入参数错误')

    return APIResponse(code=1, msg='创建失败')


# 修改term
@api_view(['POST'])
@authentication_classes([AdminTokenAuthtication])
def update(request):
    try:
        pk = request.GET.get('id', -1)
        terms = Term.objects.get(pk=pk)
    except Term.DoesNotExist:
        return APIResponse(code=1, msg='term不存在')

    data = normalize_term_dates(request.data)

    duplicate_terms = Term.objects.filter(title=data.get('title')).exclude(pk=terms.pk)
    if data.get('title') and len(duplicate_terms) > 0:
        return APIResponse(code=1, msg='该名称已存在')

    serializer = TermSerializer(terms, data=data)
    if serializer.is_valid():
        serializer.save()
        return APIResponse(code=0, msg='更新成功', data=serializer.data)
    else:
        utils.log_error(request, '修改term输入参数错误')

    return APIResponse(code=1, msg='更新失败')


# 删除term
@api_view(['POST'])
@authentication_classes([AdminTokenAuthtication])
def delete(request):
    try:
        ids = request.GET.get('ids')
        ids_arr = ids.split(',')
        Term.objects.filter(id__in=ids_arr).delete()
    except Term.DoesNotExist:
        return APIResponse(code=1, msg='term不存在')

    return APIResponse(code=0, msg='删除成功')
