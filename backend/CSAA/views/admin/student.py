import csv
import io
from datetime import datetime

from django.conf import settings
from django.db import transaction
from django.db.models import Prefetch, Q
from django.utils.dateparse import parse_date
from django.utils import timezone
from rest_framework.decorators import api_view, authentication_classes

from CSAA import utils
from CSAA.auth.authentication import AdminOrTeacherTokenAuthtication, AdminTokenAuthtication
from CSAA.handler import APIResponse
from CSAA.models import Child, CourseAdjustment, Lesson, Order, StudentAttendance, StudentComment
from CSAA.serializers import AdminStudentSerializer


@api_view(['GET'])
@authentication_classes([AdminOrTeacherTokenAuthtication])
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
@authentication_classes([AdminOrTeacherTokenAuthtication])
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
@authentication_classes([AdminOrTeacherTokenAuthtication])
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

    lesson = None
    lesson_id = request.data.get('lesson_id')
    if lesson_id:
        lesson = Lesson.objects.filter(pk=lesson_id).first()
        if not lesson:
            return APIResponse(code=1, msg='Lesson does not exist')

    lesson_date = None
    if request.data.get('lesson_date'):
        lesson_date = parse_date(str(request.data.get('lesson_date')))
        if not lesson_date:
            return APIResponse(code=1, msg='Lesson date is invalid')

    comment = StudentComment.objects.create(
        student=student,
        lesson=lesson,
        lesson_date=lesson_date,
        content=content,
        created_by=request.user,
    )
    if lesson and lesson_date:
        StudentAttendance.objects.filter(
            student=student,
            lesson=lesson,
            lesson_date=lesson_date,
        ).delete()
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


def _parse_comment_time(raw_value):
    value = str(raw_value or '').strip()
    if not value:
        return None

    formats = (
        '%Y-%m-%d %H:%M:%S',
        '%Y-%m-%d %H:%M',
        '%Y-%m-%d',
        '%m/%d/%Y %H:%M:%S',
        '%m/%d/%Y %H:%M',
        '%m/%d/%Y',
    )
    for date_format in formats:
        try:
            parsed = datetime.strptime(value, date_format)
            if date_format in ('%Y-%m-%d', '%m/%d/%Y'):
                parsed = parsed.replace(hour=12)
            if not settings.USE_TZ:
                return parsed
            return timezone.make_aware(parsed, timezone.get_current_timezone())
        except ValueError:
            continue
    return None


def _resolve_comment_student(row):
    student_id = str(row.get('student_id') or row.get('child_id') or '').strip()
    if student_id:
        return Child.objects.filter(pk=student_id).select_related('parent').first()

    student_name = str(row.get('student_name') or row.get('name') or '').strip()
    parent_username = str(row.get('parent_username') or row.get('parent') or '').strip()
    if not student_name:
        return None

    students = Child.objects.select_related('parent').filter(name__iexact=student_name)
    if parent_username:
        students = students.filter(
            Q(parent__username__iexact=parent_username)
            | Q(parent__nickname__iexact=parent_username)
        )
    return students.first()


@api_view(['POST'])
@authentication_classes([AdminTokenAuthtication])
def import_comments(request):
    rows = request.data.get('rows')
    raw_text = str(request.data.get('text', '')).strip()
    upload = request.FILES.get('file') or request.FILES.get('csv')

    if upload:
        try:
            raw_text = upload.read().decode('utf-8-sig').strip()
        except UnicodeDecodeError:
            return APIResponse(code=1, msg='CSV file must be saved as UTF-8')

    if not rows and raw_text:
        reader = csv.DictReader(io.StringIO(raw_text))
        rows = list(reader)

    if not isinstance(rows, list) or not rows:
        return APIResponse(
            code=1,
            msg='No comment rows found. Use CSV headers: student_id,comment,created_time or student_name,parent_username,comment,created_time',
        )

    created = []
    errors = []
    with transaction.atomic():
        for index, row in enumerate(rows, start=1):
            if not isinstance(row, dict):
                errors.append({'row': index, 'error': 'Invalid row format'})
                continue

            content = str(row.get('comment') or row.get('content') or '').strip()
            if not content:
                errors.append({'row': index, 'error': 'Comment cannot be empty'})
                continue
            if len(content) > 2000:
                errors.append({'row': index, 'error': 'Comment is too long'})
                continue

            student = _resolve_comment_student(row)
            if not student:
                errors.append({'row': index, 'error': 'Student not found'})
                continue

            comment = StudentComment.objects.create(
                student=student,
                content=content,
                created_by=request.user,
            )
            imported_time = _parse_comment_time(
                row.get('created_time') or row.get('date') or row.get('time')
            )
            if imported_time:
                StudentComment.objects.filter(pk=comment.pk).update(created_time=imported_time)
                comment.created_time = imported_time

            created.append(
                {
                    'id': comment.id,
                    'student_id': student.id,
                    'student_name': student.name,
                    'created_time': comment.created_time.strftime('%Y-%m-%d %H:%M:%S'),
                }
            )

    return APIResponse(
        code=0,
        msg=f'Imported {len(created)} comments',
        data={
            'created_count': len(created),
            'error_count': len(errors),
            'created': created,
            'errors': errors,
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
