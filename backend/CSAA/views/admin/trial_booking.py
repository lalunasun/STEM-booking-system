import datetime
import uuid

from django.db import transaction
from django.db.models import Q
from django.utils import timezone
from django.utils.dateparse import parse_date
from rest_framework.decorators import api_view, authentication_classes

from CSAA.auth.authentication import AdminTokenAuthtication
from CSAA.handler import APIResponse
from CSAA.models import (
    AdminTrialSession,
    Child,
    Lesson,
    Order,
    RoomCoursePermission,
    Tag,
    Term,
    Thing,
    TrialRequest,
    User,
)
from CSAA.student_creation_audit import record_student_created
from CSAA.views.admin.daily_adjustment import _occupied_count


SUBJECT_COURSES = {
    'Robotics': {'Creator', 'WeDo', 'Spike'},
    'Coding': {'Scratch JR', 'Scratch', 'Roblox', 'Python', 'Java'},
    'AI': {'AI'},
    '3D': {'3D Modelling'},
    'VEX IQ': {'VEX IQ'},
    'VEX V5': {'VEX V5'},
    'Spark Maths': {'Spark Maths'},
}
DAY_CODES = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
FLEXIBLE_SUBJECTS = {'AI', '3D', 'VEX IQ', 'VEX V5'}


def _time_range(lesson):
    try:
        start_label = lesson.thing.time.time.split('-', 1)[0].strip()
        start = datetime.time.fromisoformat(start_label.zfill(5))
        end_dt = datetime.datetime.combine(datetime.date.today(), start) + datetime.timedelta(minutes=90)
        if end_dt.date() != datetime.date.today():
            return None
        return start, end_dt.time()
    except (AttributeError, ValueError):
        return None


def _room_load_at(room, session_date, moment):
    lessons = Lesson.objects.filter(
        thing__tag=room,
        thing__day=DAY_CODES[session_date.weekday()],
        thing__status='0',
        thing__time__isnull=False,
    ).select_related('thing__time', 'thing__tag')
    seen_times = set()
    regular_load = 0
    for lesson in lessons:
        try:
            start_label, end_label = lesson.thing.time.time.split('-', 1)
            start = datetime.time.fromisoformat(start_label.strip().zfill(5))
            end = datetime.time.fromisoformat(end_label.strip().zfill(5))
        except (AttributeError, ValueError):
            continue
        if start <= moment < end and lesson.thing.time_id not in seen_times:
            seen_times.add(lesson.thing.time_id)
            regular_load += _occupied_count(lesson, session_date, include_admin_trial=False)
    trial_load = AdminTrialSession.objects.filter(
        Q(room=room) | Q(room__isnull=True, lesson__thing__tag=room),
        session_date=session_date,
        status='active',
        starts_at__lte=moment,
        ends_at__gt=moment,
    ).count()
    return regular_load + trial_load


def _active_terms(session_date):
    return Term.objects.filter(
        expect_time__date__lte=session_date,
        return_time__date__gte=session_date,
    )


def _flexible_rooms(subject, session_date):
    course_titles = SUBJECT_COURSES.get(subject, set())
    return Tag.objects.filter(
        seat__gt=0,
        roomcoursepermission__term__in=_active_terms(session_date),
        roomcoursepermission__courses__active=True,
        roomcoursepermission__courses__title__in=course_titles,
    ).distinct().order_by('title')


def _parse_thing_range(thing):
    try:
        start_label, end_label = thing.time.time.split('-', 1)
        return (
            datetime.time.fromisoformat(start_label.strip().zfill(5)),
            datetime.time.fromisoformat(end_label.strip().zfill(5)),
        )
    except (AttributeError, ValueError):
        return None


def _flexible_start_times(session_date):
    starts = set()
    things = Thing.objects.filter(
        day=DAY_CODES[session_date.weekday()], status='0', time__isnull=False,
    ).select_related('time')
    for thing in things:
        time_range = _parse_thing_range(thing)
        if time_range:
            starts.add(time_range[0])
    return sorted(starts)


def _has_regular_class(room, session_date, start, end):
    things = Thing.objects.filter(
        tag=room,
        day=DAY_CODES[session_date.weekday()],
        status='0',
        time__isnull=False,
        thing_lesson__isnull=False,
    ).select_related('time').distinct()
    return any(
        time_range and time_range[0] < end and time_range[1] > start
        for time_range in (_parse_thing_range(thing) for thing in things)
    )


def _flexible_options(subject, session_date):
    if subject not in FLEXIBLE_SUBJECTS:
        return []
    course_name = next(iter(SUBJECT_COURSES[subject]))
    data = []
    for start in _flexible_start_times(session_date):
        end_dt = datetime.datetime.combine(session_date, start) + datetime.timedelta(minutes=90)
        if end_dt.date() != session_date:
            continue
        end = end_dt.time()
        for room in _flexible_rooms(subject, session_date):
            has_regular_class = _has_regular_class(room, session_date, start, end)
            data.append({
                'mode': 'flexible',
                'option_key': f'flexible:{room.id}:{start.strftime("%H:%M")}',
                'course': course_name,
                'room_id': room.id,
                'room': room.title,
                'start': start.strftime('%H:%M'),
                'end': end.strftime('%H:%M'),
                'remaining': _remaining(room, session_date, start, end),
                'has_regular_class': has_regular_class,
                'teacher_confirmation_required': not has_regular_class,
            })
    return data


def _remaining(room, session_date, start, end, extra_sessions=()):
    if not room.seat:
        return 0
    current = datetime.datetime.combine(session_date, start)
    finish = datetime.datetime.combine(session_date, end)
    remaining = int(room.seat)
    while current < finish:
        moment = current.time()
        extra = sum(
            item['room_id'] == room.id and item['date'] == session_date and
            item['start'] <= moment < item['end']
            for item in extra_sessions
        )
        remaining = min(remaining, int(room.seat) - _room_load_at(room, session_date, moment) - extra)
        current += datetime.timedelta(minutes=15)
    return remaining


def _student_has_conflict(student, session_date, start, end, extra_sessions=()):
    if any(item['date'] == session_date and item['start'] < end and item['end'] > start for item in extra_sessions):
        return True
    if AdminTrialSession.objects.filter(
        student=student, session_date=session_date, status='active',
        starts_at__lt=end, ends_at__gt=start,
    ).exists():
        return True
    orders = Order.objects.filter(
        child=student, status=6, thing__day=DAY_CODES[session_date.weekday()],
        expect_time__date__lte=session_date, return_time__date__gte=session_date,
        trial_package_requests__isnull=True,
    ).select_related('thing__time')
    for order in orders:
        try:
            slot_start, slot_end = order.thing.time.time.split('-', 1)
            if datetime.time.fromisoformat(slot_start.strip().zfill(5)) < end and datetime.time.fromisoformat(slot_end.strip().zfill(5)) > start:
                return True
        except (AttributeError, ValueError):
            continue
    legacy_trials = TrialRequest.objects.filter(
        child=student, status__in=['approved', 'scheduled'], package_order__status__in=[2, 6],
    ).select_related('package_order', 'robotics_class__time', 'coding_class__time')
    for trial in legacy_trials:
        for thing in (trial.robotics_class, trial.coding_class):
            if not thing or thing.day not in DAY_CODES:
                continue
            first_date = trial.package_order.order_time.date() + datetime.timedelta(
                days=(DAY_CODES.index(thing.day) - trial.package_order.order_time.date().weekday()) % 7
            )
            if first_date != session_date:
                continue
            try:
                slot_start, slot_end = thing.time.time.split('-', 1)
                if datetime.time.fromisoformat(slot_start.strip().zfill(5)) < end and datetime.time.fromisoformat(slot_end.strip().zfill(5)) > start:
                    return True
            except (AttributeError, ValueError):
                continue
    return False


@api_view(['GET'])
@authentication_classes([AdminTokenAuthtication])
def options(request):
    session_date = parse_date(request.GET.get('date', ''))
    subject = request.GET.get('subject', '')
    if not session_date or subject not in SUBJECT_COURSES:
        return APIResponse(code=1, msg='Select a valid subject and date')
    mode = request.GET.get('mode', 'existing')
    if mode == 'flexible':
        if subject not in FLEXIBLE_SUBJECTS:
            return APIResponse(code=1, msg='Flexible trial slots are only available for AI, 3D, VEX IQ and VEX V5')
        return APIResponse(code=0, msg='Query successful', data=_flexible_options(subject, session_date))
    student = None
    if request.GET.get('student_id'):
        try:
            student = Child.objects.get(id=int(request.GET['student_id']))
        except (Child.DoesNotExist, TypeError, ValueError):
            return APIResponse(code=1, msg='Student does not exist')
    lessons = Lesson.objects.filter(
        thing__title__in=SUBJECT_COURSES[subject],
        thing__day=DAY_CODES[session_date.weekday()],
        thing__status='0',
        thing__tag__isnull=False,
        thing__time__isnull=False,
    ).select_related('thing__tag', 'thing__time').order_by('thing__time__time', 'thing__tag__title')
    data = []
    for lesson in lessons:
        time_range = _time_range(lesson)
        if not time_range:
            continue
        start, end = time_range
        data.append({
            'mode': 'existing',
            'option_key': f'existing:{lesson.id}',
            'lesson_id': lesson.id,
            'course': lesson.thing.title,
            'room': lesson.thing.tag.title,
            'start': start.strftime('%H:%M'),
            'end': end.strftime('%H:%M'),
            'remaining': _remaining(lesson.thing.tag, session_date, start, end),
            'student_conflict': _student_has_conflict(student, session_date, start, end) if student else False,
        })
    return APIResponse(code=0, msg='Query successful', data=data)


@api_view(['GET'])
@authentication_classes([AdminTokenAuthtication])
def list_api(request):
    student_id = request.GET.get('student_id')
    if not student_id:
        return APIResponse(code=1, msg='Student is required')
    sessions = AdminTrialSession.objects.filter(student_id=student_id).select_related(
        'lesson__thing__tag', 'lesson__thing__time', 'room'
    ).order_by('-created_time', 'session_index')
    packages = {}
    for item in sessions:
        key = str(item.package_key)
        package = packages.setdefault(key, {'package_key': key, 'status': item.status, 'sessions': []})
        thing = item.lesson.thing if item.lesson_id else None
        package['sessions'].append({
            'date': item.session_date.strftime('%Y-%m-%d'),
            'course': item.course_name or (thing.title if thing else ''),
            'room': item.room.title if item.room_id else (thing.tag.title if thing and thing.tag else ''),
            'time': f'{item.starts_at.strftime("%H:%M")}-{item.ends_at.strftime("%H:%M")}',
            'booking_mode': item.booking_mode,
            'teacher_confirmation_required': item.teacher_confirmation_required,
        })
    return APIResponse(code=0, msg='Query successful', data=list(packages.values()))


@api_view(['POST'])
@authentication_classes([AdminTokenAuthtication])
@transaction.atomic
def create(request):
    if request.data.get('student_id'):
        return APIResponse(code=1, msg='Create a new trial student instead of booking for an existing student')
    student_name = str(request.data.get('student_name') or '').strip()
    if not student_name or len(student_name) > 30:
        return APIResponse(code=1, msg='Student name is required and must be 30 characters or fewer')
    try:
        age = int(request.data['age']) if request.data.get('age') not in (None, '') else None
    except (TypeError, ValueError):
        return APIResponse(code=1, msg='Enter a valid age')
    if age is not None and (age < 1 or age > 99):
        return APIResponse(code=1, msg='Age must be between 1 and 99')
    parent = None
    if request.data.get('parent_id'):
        parent = User.objects.filter(id=request.data['parent_id'], role='1').first()
        if not parent:
            return APIResponse(code=1, msg='Selected parent account does not exist')
    sessions = request.data.get('sessions')
    if not isinstance(sessions, list) or len(sessions) != 2:
        return APIResponse(code=1, msg='A three-hour package needs two 90-minute sessions')
    note = str(request.data.get('note') or '').strip()[:500]
    prepared = []
    for item in sessions:
        session_date = parse_date(str(item.get('date') or ''))
        mode = str(item.get('mode') or 'existing')
        if mode == 'flexible':
            subject = str(item.get('subject') or '')
            if not session_date:
                return APIResponse(code=1, msg='Select a valid date for the flexible trial slot')
            try:
                room = _flexible_rooms(subject, session_date).get(id=item.get('room_id'))
                start = datetime.time.fromisoformat(str(item.get('start') or '').strip().zfill(5))
            except (Tag.DoesNotExist, AttributeError, TypeError, ValueError):
                return APIResponse(code=1, msg='Selected flexible trial slot is not available')
            if subject not in FLEXIBLE_SUBJECTS or start not in _flexible_start_times(session_date):
                return APIResponse(code=1, msg='Selected flexible trial slot is not available')
            end_dt = datetime.datetime.combine(session_date, start) + datetime.timedelta(minutes=90)
            if end_dt.date() != session_date:
                return APIResponse(code=1, msg='Selected flexible trial slot is not available')
            end = end_dt.time()
            prepared.append({
                'mode': 'flexible',
                'lesson': None,
                'room': room,
                'room_id': room.id,
                'course_name': next(iter(SUBJECT_COURSES[subject])),
                'date': session_date,
                'start': start,
                'end': end,
                'teacher_confirmation_required': not _has_regular_class(room, session_date, start, end),
            })
            continue
        try:
            lesson = Lesson.objects.select_related('thing__tag', 'thing__time').get(
                id=item.get('lesson_id'), thing__status='0'
            )
        except (Lesson.DoesNotExist, AttributeError, TypeError, ValueError):
            return APIResponse(code=1, msg='Selected trial class does not exist')
        if not session_date or lesson.thing.day != DAY_CODES[session_date.weekday()]:
            return APIResponse(code=1, msg='Class weekday does not match the selected date')
        if not any(lesson.thing.title in courses for courses in SUBJECT_COURSES.values()):
            return APIResponse(code=1, msg='This course is not in the trial package')
        time_range = _time_range(lesson)
        if not time_range or not lesson.thing.tag_id:
            return APIResponse(code=1, msg='Trial class needs a room and valid start time')
        start, end = time_range
        prepared.append({
            'mode': 'existing',
            'lesson': lesson,
            'room': lesson.thing.tag,
            'room_id': lesson.thing.tag_id,
            'course_name': lesson.thing.title,
            'date': session_date,
            'start': start,
            'end': end,
            'teacher_confirmation_required': False,
        })

    list(Tag.objects.select_for_update().filter(id__in=sorted({item['room_id'] for item in prepared})))
    checked = []
    for item in prepared:
        if any(previous['date'] == item['date'] and previous['start'] < item['end'] and previous['end'] > item['start'] for previous in checked):
            return APIResponse(code=1, msg='Trial sessions cannot overlap')
        if _remaining(item['room'], item['date'], item['start'], item['end'], checked) < 1:
            return APIResponse(code=1, msg=f'{item["room"].title} is full during this 90-minute trial')
        checked.append(item)

    student = Child.objects.create(name=student_name, age=age, parent=parent, remark=note)
    record_student_created(student, 'admin_trial', request.user)
    package_key = uuid.uuid4()
    for index, item in enumerate(prepared, start=1):
        AdminTrialSession.objects.create(
            package_key=package_key,
            session_index=index,
            student=student,
            lesson=item['lesson'],
            room=item['room'],
            course_name=item['course_name'],
            booking_mode=item['mode'],
            teacher_confirmation_required=item['teacher_confirmation_required'],
            session_date=item['date'],
            starts_at=item['start'],
            ends_at=item['end'],
            note=note,
            created_by=request.user,
        )
    return APIResponse(code=0, msg='Trial student and package created', data={
        'package_key': str(package_key), 'student_id': student.id,
    })


@api_view(['POST'])
@authentication_classes([AdminTokenAuthtication])
@transaction.atomic
def cancel(request):
    try:
        package_key = uuid.UUID(str(request.data.get('package_key')))
    except (TypeError, ValueError):
        return APIResponse(code=1, msg='Invalid trial package')
    sessions = AdminTrialSession.objects.select_for_update().filter(package_key=package_key, status='active')
    if not sessions.exists():
        return APIResponse(code=1, msg='Active trial package does not exist')
    sessions.update(status='canceled', canceled_by=request.user, canceled_time=timezone.now())
    return APIResponse(code=0, msg='Trial package canceled')
