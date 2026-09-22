import csv
import io
import json
from datetime import datetime, time, timedelta
import re
from zoneinfo import ZoneInfo

from django.conf import settings
from django.db import transaction
from django.db.models import Prefetch, Q
from django.utils.dateparse import parse_date
from django.utils import timezone
from rest_framework.decorators import api_view, authentication_classes

from CSAA import utils
from CSAA.auth.authentication import AdminOrTeacherTokenAuthtication, AdminTokenAuthtication
from CSAA.course_conflicts import student_slot_conflict
from CSAA.handler import APIResponse
from CSAA.models import Child, CourseAdjustment, Lesson, OpLog, Order, StudentAttendance, StudentComment, Term, Thing, User, Tag
from CSAA.room_permissions import candidate_classes, course_allowed
from CSAA.serializers import AdminStudentSerializer
from CSAA.student_creation_audit import STUDENT_CREATED_EVENT, record_student_created


STUDENT_AUDIT_SOURCE_TIMEZONE = ZoneInfo('Asia/Shanghai')
STUDENT_AUDIT_DISPLAY_TIMEZONE = ZoneInfo('America/Toronto')


def _format_student_audit_time(value):
    if not value:
        return ''
    if timezone.is_naive(value):
        value = value.replace(tzinfo=STUDENT_AUDIT_SOURCE_TIMEZONE)
    return value.astimezone(STUDENT_AUDIT_DISPLAY_TIMEZONE).strftime('%Y-%m-%d %H:%M')


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
@authentication_classes([AdminTokenAuthtication])
def creation_log(request):
    events = list(OpLog.objects.filter(re_url=STUDENT_CREATED_EVENT).order_by('-re_time')[:100])
    parsed = []
    for event in events:
        try:
            payload = json.loads(event.re_content or '{}')
            student_id = int(payload['student_id'])
        except (TypeError, ValueError, KeyError):
            continue
        parsed.append((event, student_id, payload))

    students = Child.objects.in_bulk([student_id for _, student_id, _ in parsed])
    actors = User.objects.in_bulk([
        payload['actor_id'] for _, _, payload in parsed if payload.get('actor_id')
    ])
    rows = []
    for event, student_id, payload in parsed:
        actor = actors.get(payload.get('actor_id'))
        student = students.get(student_id)
        rows.append({
            'id': f'created-{event.id}',
            'created_time': _format_student_audit_time(event.re_time),
            'student_id': student_id,
            'student_name': student.name if student else None,
            'source': payload.get('source', 'other'),
            'actor': (actor.nickname or actor.username) if actor else None,
            'confirmed': True,
        })

    legacy = OpLog.objects.filter(re_url__in=[
        '/CSAA/admin/student/create',
        '/CSAA/admin/student/quickCreate',
        '/CSAA/index/child/create',
    ])
    first_event = OpLog.objects.filter(re_url=STUDENT_CREATED_EVENT).order_by('re_time').first()
    if first_event:
        legacy = legacy.filter(re_time__lt=first_event.re_time)
    for entry in legacy.order_by('-re_time')[:50]:
        try:
            legacy_name = json.loads(entry.re_content or '{}').get('name')
        except (TypeError, ValueError, AttributeError):
            legacy_name = None
        rows.append({
            'id': f'legacy-{entry.id}',
            'created_time': _format_student_audit_time(entry.re_time),
            'student_id': None,
            'student_name': legacy_name if isinstance(legacy_name, str) else None,
            'source': (
                'admin_quick' if entry.re_url.endswith('/quickCreate') else
                'parent' if '/index/' in entry.re_url else 'admin'
            ),
            'actor': None,
            'confirmed': False,
        })
    rows.sort(key=lambda row: row['created_time'], reverse=True)
    return APIResponse(code=0, msg='Student addition history', data=rows)


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


def _student_payload(request):
    """Normalize the small admin form before passing it to the model serializer."""
    data = request.data.copy()
    name = str(data.get('name', '')).strip()
    if not name:
        return None, 'Student name is required'
    if len(name) > 30:
        return None, 'Student name is too long'

    data['name'] = name
    parent_id = data.get('parent')
    if parent_id in (None, ''):
        data['parent'] = None
    else:
        try:
            parent = User.objects.get(pk=parent_id, role='1', status='0')
        except (User.DoesNotExist, TypeError, ValueError):
            return None, 'Selected parent account does not exist or is inactive'
        data['parent'] = parent.id

    for field in ('gender', 'remark'):
        if data.get(field) == '':
            data[field] = None
    return data, None


def _enrollment_window(term, params):
    start_value = params.get('start_date')
    end_value = params.get('end_date')
    if not term.expect_time or not term.return_time:
        if start_value or end_value:
            return None, 'This term has no dates to contain a custom enrollment'
        return (None, None), None

    try:
        start_date = parse_date(start_value) if start_value else term.expect_time.date()
        end_date = parse_date(end_value) if end_value else term.return_time.date()
    except ValueError:
        return None, 'Use YYYY-MM-DD for class dates'
    if start_date is None or end_date is None:
        return None, 'Use YYYY-MM-DD for class dates'
    if start_date > end_date:
        return None, 'Class start date must be on or before the end date'
    if start_date < term.expect_time.date() or end_date > term.return_time.date():
        return None, 'Class dates must be within the selected term'

    start = max(term.expect_time, datetime.combine(start_date, time.min)) if start_value else term.expect_time
    end = min(term.return_time, datetime.combine(end_date, time.max)) if end_value else term.return_time
    return (start, end), None


def _active_enrollment_count(thing, term, start_date=None, end_date=None):
    """Count peak concurrent students in the requested date and room/time window."""
    if not thing or not thing.tag or not thing.time or not thing.day:
        return Order.objects.filter(
            thing=thing,
            term=term,
            child__isnull=False,
            status__in=[2, 6],
            trial_package_requests__isnull=True,
        ).count()

    def minutes(label):
        match = re.fullmatch(r'\s*(\d{1,2}):(\d{2})\s*-\s*(\d{1,2}):(\d{2})\s*', label or '')
        if not match:
            return None
        h1, m1, h2, m2 = map(int, match.groups())
        return h1 * 60 + m1, h2 * 60 + m2

    target = minutes(thing.time.time)
    orders = Order.objects.filter(
        thing__tag=thing.tag, thing__day=thing.day,
        child__isnull=False,
        status__in=[2, 6],
        trial_package_requests__isnull=True,
    ).select_related('thing__time', 'term')
    intervals = []
    for order in orders:
        span = minutes(order.thing.time.time) if order.thing.time else None
        if target and span:
            left, right = max(target[0], span[0]), min(target[1], span[1])
            if left >= right:
                continue
        elif order.thing.time_id != thing.time_id:
            continue
        else:
            left, right = 0, 1
        start = order.expect_time or (order.term.expect_time if order.term else None)
        end = order.return_time or (order.term.return_time if order.term else None)
        start = max(start.date() if start else datetime.min.date(),
                    start_date or (term.expect_time.date() if term.expect_time else datetime.min.date()))
        end = min(end.date() if end else datetime.max.date(),
                  end_date or (term.return_time.date() if term.return_time else datetime.max.date()))
        if start <= end:
            weekday = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'].index(thing.day)
            first_day = start + timedelta(days=(weekday - start.weekday()) % 7)
            if first_day <= end:
                intervals.append((first_day, end, left, right, order.child_id))
    # Peak concurrent students across overlapping terms and partial-hour classes.
    return max((
        len({child for begin, end, left, right, child in intervals
             if begin <= date <= end and left <= minute < right})
        for date in {item[0] for item in intervals}
        for minute in {item[2] for item in intervals}
    ), default=0)


def _slot_payload(thing, term, start_date=None, end_date=None):
    capacity = thing.tag.seat if thing.tag else None
    enrolled_count = _active_enrollment_count(thing, term, start_date, end_date)
    available_seats = None if capacity is None else max(int(capacity) - enrolled_count, 0)
    return {
        'id': thing.id,
        'slot_key': f'{thing.tag_id}:{thing.day}:{thing.time_id}',
        'room_id': thing.tag_id,
        'time_id': thing.time_id,
        'new_class': thing.pk is None,
        'title': thing.title,
        'day': thing.day,
        'time': thing.time.time if thing.time else None,
        'room': thing.tag.title if thing.tag else None,
        'capacity': capacity,
        'enrolled_count': enrolled_count,
        'available_seats': available_seats,
        'term_id': term.id,
        'term_title': term.title,
    }


@api_view(['GET'])
@authentication_classes([AdminTokenAuthtication])
def available_slots(request):
    """Return existing class instances that match the administrator's preferences."""
    term_id = request.GET.get('term')
    course = str(request.GET.get('course') or '').strip()
    day = str(request.GET.get('day') or '').strip()
    time_id = request.GET.get('time')

    if not term_id or not course:
        return APIResponse(code=1, msg='Term and course are required')

    try:
        term = Term.objects.get(pk=term_id)
    except (Term.DoesNotExist, TypeError, ValueError):
        return APIResponse(code=1, msg='Term does not exist')

    window, error = _enrollment_window(term, request.GET)
    if error:
        return APIResponse(code=1, msg=error)
    start, end = window

    try:
        things = candidate_classes(term, course, day, int(time_id) if time_id else None)
    except (TypeError, ValueError):
        return APIResponse(code=1, msg='Invalid time')
    slots = [_slot_payload(thing, term, start.date() if start else None,
                           end.date() if end else None) for thing in things]
    return APIResponse(code=0, msg='Available slots loaded', data=slots)


@api_view(['POST'])
@authentication_classes([AdminTokenAuthtication])
@transaction.atomic
def quick_create(request):
    """Create an administrator-entered student and their first active enrollment."""
    data, error = _student_payload(request)
    if error:
        return APIResponse(code=1, msg=error)

    try:
        term = Term.objects.get(pk=request.data.get('term'))
        if request.data.get('thing'):
            thing = Thing.objects.select_related('tag', 'time').get(
                pk=request.data.get('thing'), status='0',
            )
            room_id = thing.tag_id
        else:
            room_id = int(request.data.get('room'))
            thing = None
        Tag.objects.select_for_update().get(pk=room_id)
        if thing is None:
            candidates = candidate_classes(
                term, str(request.data.get('course') or '').strip(),
                request.data.get('day'), int(request.data.get('time')),
            )
            thing = next((item for item in candidates if item.tag_id == room_id), None)
            if thing is None:
                return APIResponse(code=1, msg='This room or time is no longer available')
    except (Term.DoesNotExist, Thing.DoesNotExist, Tag.DoesNotExist, TypeError, ValueError):
        return APIResponse(code=1, msg='Selected term or class does not exist')

    window, error = _enrollment_window(term, request.data)
    if error:
        return APIResponse(code=1, msg=error)
    start, end = window

    if not course_allowed(room_id, term, thing.title):
        return APIResponse(code=1, msg='This course is no longer allowed in this room for the selected term')
    parent = None
    if data.get('parent'):
        parent = User.objects.get(pk=data['parent'])

    if parent and Child.objects.filter(name=data['name'], parent=parent).exists():
        return APIResponse(code=1, msg='This parent already has a student with the same name')

    capacity = thing.tag.seat if thing.tag else None
    if capacity is not None and _active_enrollment_count(
        thing, term, start.date() if start else None, end.date() if end else None,
    ) >= int(capacity):
        return APIResponse(code=1, msg=f'{thing.title} is full for {thing.day} {thing.time.time if thing.time else ""}')

    with transaction.atomic():
        if thing.pk is None:
            template = Thing.objects.filter(title__iexact=thing.title, status='0').first()
            if template:
                thing.classification = template.classification
                thing.cover = template.cover
                thing.price = template.price
            thing.save()
            Lesson.objects.get_or_create(thing=thing)
        student = Child.objects.create(
            parent=parent,
            name=data['name'],
            age=data.get('age'),
            gender=data.get('gender'),
            remark=data.get('remark'),
        )
        Order.objects.create(
            order_number=str(utils.get_timestamp()),
            user=parent,
            thing=thing,
            count=1,
            num=1,
            child=student,
            expect_time=start,
            return_time=end,
            term=term,
            amount='0',
            status=6,
            pay_time=timezone.now(),
            receiver_name=student.name,
            receiver_phone=parent.mobile if parent else None,
            remark='Admin created',
        )
        record_student_created(student, 'admin_quick', request.user)

    return APIResponse(
        code=0,
        msg='Student and first class created',
        data={
            'student_id': student.id,
            'student_name': student.name,
            'slot': _slot_payload(thing, term, start.date() if start else None,
                                  end.date() if end else None),
        },
    )


@api_view(['POST'])
@authentication_classes([AdminTokenAuthtication])
@transaction.atomic
def create(request):
    data, error = _student_payload(request)
    if error:
        return APIResponse(code=1, msg=error)

    parent_id = data.get('parent')
    if parent_id and Child.objects.filter(name=data['name'], parent_id=parent_id).exists():
        return APIResponse(code=1, msg='This parent already has a student with the same name')

    serializer = AdminStudentSerializer(data=data)
    if serializer.is_valid():
        student = serializer.save()
        record_student_created(student, 'admin', request.user)
        return APIResponse(code=0, msg='创建成功', data=serializer.data)

    utils.log_error(request, f'添加student输入参数错误: {serializer.errors}')
    return APIResponse(code=1, msg='创建失败，请检查学生资料')


@api_view(['POST'])
@authentication_classes([AdminTokenAuthtication])
def update(request):
    try:
        pk = request.GET.get('id', -1)
        student = Child.objects.get(pk=pk)
    except Child.DoesNotExist:
        return APIResponse(code=1, msg='Student不存在')

    data, error = _student_payload(request)
    if error:
        return APIResponse(code=1, msg=error)

    parent_id = data.get('parent')
    if parent_id and Child.objects.filter(
        name=data['name'], parent_id=parent_id,
    ).exclude(pk=student.pk).exists():
        return APIResponse(code=1, msg='This parent already has a student with the same name')

    serializer = AdminStudentSerializer(student, data=data)
    if serializer.is_valid():
        serializer.save()
        if 'parent' in request.data:
            Order.objects.filter(child=student).update(
                user=student.parent,
                receiver_phone=student.parent.mobile if student.parent else None,
            )
        return APIResponse(code=0, msg='更新成功', data=serializer.data)

    utils.log_error(request, f'修改student输入参数错误: {serializer.errors}')
    return APIResponse(code=1, msg='更新失败，请检查学生资料')


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
