from rest_framework.decorators import api_view, authentication_classes

from CSAA import utils
from CSAA.auth.authentication import AdminTokenAuthtication
from CSAA.handler import APIResponse
from CSAA.models import Tag, Term, Course, Thing, RoomCoursePermission
from django.db import transaction
from CSAA.serializers import TagSerializer


# Room列表
@api_view(['GET', 'POST'])
@authentication_classes([AdminTokenAuthtication])
def course_permissions(request):
    params = request.query_params if request.method == 'GET' else request.data
    try:
        room = Tag.objects.get(pk=params.get('room'))
        term = Term.objects.get(pk=params.get('term'))
    except (Tag.DoesNotExist, Term.DoesNotExist, ValueError, TypeError):
        return APIResponse(code=1, msg='Select a valid room and term')
    if request.method == 'POST':
        ids = params.get('course_ids')
        note = str(params.get('note') or '').strip()
        if not isinstance(ids, list) or len(note) > 500:
            return APIResponse(code=1, msg='Invalid courses or note')
        try:
            ids = {int(value) for value in ids}
        except (ValueError, TypeError):
            return APIResponse(code=1, msg='Invalid courses')
        courses = Course.objects.filter(id__in=ids, active=True)
        if courses.count() != len(ids):
            return APIResponse(code=1, msg='Select active courses')
        with transaction.atomic():
            Tag.objects.select_for_update().get(pk=room.pk)
            rule, _ = RoomCoursePermission.objects.get_or_create(room=room, term=term)
            rule.courses.set(courses)
            rule.note = note
            rule.updated_by = request.user
            rule.save()
    rule = RoomCoursePermission.objects.filter(room=room, term=term).first()
    titles = Thing.objects.filter(tag=room, status='0').values_list('title', flat=True)
    inferred = {str(title).casefold() for title in titles}
    suggested = [course.id for course in Course.objects.filter(active=True) if course.title.casefold() in inferred]
    return APIResponse(code=0, msg='Saved' if request.method == 'POST' else 'OK', data={
        'configured': rule is not None,
        'course_ids': list(rule.courses.values_list('id', flat=True)) if rule else [],
        'suggested_course_ids': suggested,
        'note': rule.note if rule else '',
        'updated_at': rule.updated_at.isoformat() if rule else None,
    })


@api_view(['GET'])
def list_api(request):
    if request.method == 'GET':
        tags = Tag.objects.all().order_by('-create_time')
        serializer = TagSerializer(tags, many=True)
        return APIResponse(code=0, msg='查询成功', data=serializer.data)


# 创建Room
@api_view(['POST'])
@authentication_classes([AdminTokenAuthtication])
def create(request):
    # 查询当前Room是否已经存在
    tags = Tag.objects.filter(title=request.data['title'])
    if len(tags) > 0:
        return APIResponse(code=1, msg='该名称已存在')

    serializer = TagSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return APIResponse(code=0, msg='创建成功', data=serializer.data)
    else:
        utils.log_error(request, '添加Room输入参数错误')

    return APIResponse(code=1, msg='创建失败')


# 修改Room
@api_view(['POST'])
@authentication_classes([AdminTokenAuthtication])
def update(request):
    try:
        pk = request.GET.get('id', -1)
        tags = Tag.objects.get(pk=pk)
    except Tag.DoesNotExist:
        return APIResponse(code=1, msg='Room不存在')

    serializer = TagSerializer(tags, data=request.data)
    if serializer.is_valid():
        serializer.save()
        return APIResponse(code=0, msg='更新成功', data=serializer.data)
    else:
        utils.log_error(request, '修改Room输入参数错误')

    return APIResponse(code=1, msg='更新失败')


# 删除Room
@api_view(['POST'])
@authentication_classes([AdminTokenAuthtication])
def delete(request):
    try:
        ids = request.GET.get('ids')
        ids_arr = ids.split(',')
        Tag.objects.filter(id__in=ids_arr).delete()
    except Tag.DoesNotExist:
        return APIResponse(code=1, msg='Room不存在')

    return APIResponse(code=0, msg='删除成功')
