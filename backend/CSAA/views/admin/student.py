from django.db.models import Prefetch, Q
from rest_framework.decorators import api_view, authentication_classes

from CSAA import utils
from CSAA.auth.authentication import AdminTokenAuthtication
from CSAA.handler import APIResponse
from CSAA.models import Child, CourseAdjustment, Order, StudentComment
from CSAA.serializers import AdminStudentSerializer


@api_view(['GET'])
def list_api(request):
    keyword = request.GET.get('keyword', '')
    students = Child.objects.select_related('parent').prefetch_related(
        Prefetch(
            'child_order',
            queryset=Order.objects.filter(status__in=[2, 6]).select_related(
                'thing',
                'thing__time',
                'thing__tag',
                'term',
            ),
            to_attr='prefetched_active_orders',
        ),
        Prefetch(
            'course_adjustments',
            queryset=CourseAdjustment.objects.filter(
                request_type='cancel_class',
            ).only('id', 'student_id'),
            to_attr='prefetched_absences',
        ),
    ).all().order_by('parent__username', 'name')

    if keyword:
        students = students.filter(
            Q(name__contains=keyword)
            | Q(parent__username__contains=keyword)
            | Q(parent__nickname__contains=keyword)
            | Q(parent__mobile__contains=keyword)
        )

    serializer = AdminStudentSerializer(
        students,
        many=True,
        context={'summary_only': True},
    )
    return APIResponse(code=0, msg='查询成功', data=serializer.data)


@api_view(['GET'])
@authentication_classes([AdminTokenAuthtication])
def detail(request):
    try:
        student = Child.objects.select_related('parent').get(pk=request.GET.get('id'))
    except (Child.DoesNotExist, TypeError, ValueError):
        return APIResponse(code=1, msg='Student does not exist')

    data = AdminStudentSerializer(student).data
    comments = StudentComment.objects.filter(student=student).select_related(
        'created_by',
    ).order_by('-created_time')
    data['comments'] = [
        {
            'id': comment.id,
            'content': comment.content,
            'created_by': (
                comment.created_by.nickname or comment.created_by.username
                if comment.created_by
                else 'Unknown administrator'
            ),
            'created_time': comment.created_time.strftime('%Y-%m-%d %H:%M:%S'),
        }
        for comment in comments
    ]
    return APIResponse(code=0, msg='Success', data=data)


@api_view(['POST'])
@authentication_classes([AdminTokenAuthtication])
def create_comment(request):
    content = str(request.data.get('content', '')).strip()
    if not content:
        return APIResponse(code=1, msg='Comment cannot be empty')
    if len(content) > 2000:
        return APIResponse(code=1, msg='Comment is too long')

    try:
        student = Child.objects.get(pk=request.data.get('student_id'))
    except (Child.DoesNotExist, TypeError, ValueError):
        return APIResponse(code=1, msg='Student does not exist')

    comment = StudentComment.objects.create(
        student=student,
        content=content,
        created_by=request.user,
    )
    return APIResponse(
        code=0,
        msg='Comment saved',
        data={
            'id': comment.id,
            'content': comment.content,
            'created_by': request.user.nickname or request.user.username,
            'created_time': comment.created_time.strftime('%Y-%m-%d %H:%M:%S'),
        },
    )


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
