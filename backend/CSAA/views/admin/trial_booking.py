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
from CSAA.room_permissions import blocked_day_codes
from CSAA.trial_packages import (
    TRIAL_PACKAGE_TEMPLATES,
    infer_trial_package_type,
    public_trial_package_templates,
    trial_package_label,
)
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
FLEXIBLE_SUBJECTS = set(SUBJECT_COURSES)
TRIAL_DAY_HOURS = {
    1: (datetime.time(16, 0), datetime.time(19, 0)),
    2: (datetime.time(16, 0), datetime.time(19, 0)),
    3: (datetime.time(16, 0), datetime.time(19, 0)),
    4: (datetime.time(16, 0), datetime.time(19, 0)),
    5: (datetime.time(9, 0), datetime.time(18, 0)),
    6: (datetime.time(9, 0), datetime.time(18, 0)),
}


def _trial_time_allowed(session_date, start, end):
    bounds = TRIAL_DAY_HOURS.get(session_date.weekday())
    return bool(bounds and bounds[0] <= start < end <= bounds[1])


def _time_range(lesson, session_date, duration_minutes=90):
    try:
        start_label = lesson.thing.time.time.split('-', 1)[0].strip()
        start = datetime.time.fromisoformat(start_label.zfill(5))
        end_dt = datetime.datetime.combine(session_date, start) + datetime.timedelta(minutes=duration_minutes)
        if end_dt.date() != session_date or not _trial_time_allowed(
            session_date, start, end_dt.time(),
        ):
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


def _allowed_room_courses(subject, session_date):
    course_titles = {
        title.casefold(): title for title in SUBJECT_COURSES.get(subject, set())
    }
    day = DAY_CODES[session_date.weekday()]
    rules = RoomCoursePermission.objects.filter(
        term__in=_active_terms(session_date),
        room__seat__gt=0,
    ).select_related('room').prefetch_related('courses').distinct()
    allowed = {}
    for rule in rules:
        if day in blocked_day_codes(rule):
            continue
        for course in rule.courses.all():
            key = (course.title or '').strip().casefold()
            if course.active and key in course_titles:
                allowed[(rule.room_id, key)] = (rule.room, course.title)
    return sorted(allowed.values(), key=lambda item: (item[1].casefold(), item[0].title.casefold()))


def _course_allowed_for_date(room_id, course_title, session_date):
    day = DAY_CODES[session_date.weekday()]
    rules = list(RoomCoursePermission.objects.filter(
        room_id=room_id,
        term__in=_active_terms(session_date),
    ).prefetch_related('courses'))
    if not rules:
        return True
    wanted = course_title.strip().casefold()
    return any(
        day not in blocked_day_codes(rule) and any(
            course.active and (course.title or '').strip().casefold() == wanted
            for course in rule.courses.all()
        )
        for rule in rules
    )


def _parse_thing_range(thing):
    try:
        start_label, end_label = thing.time.time.split('-', 1)
        return (
            datetime.time.fromisoformat(start_label.strip().zfill(5)),
            datetime.time.fromisoformat(end_label.strip().zfill(5)),
        )
    except (AttributeError, ValueError):
        return None


def _flexible_start_times(session_date, duration_minutes=90, start_interval_minutes=30):
    bounds = TRIAL_DAY_HOURS.get(session_date.weekday())
    if not bounds:
        return []
    cursor = datetime.datetime.combine(session_date, bounds[0])
    finish = datetime.datetime.combine(session_date, bounds[1])
    starts = []
    while cursor + datetime.timedelta(minutes=duration_minutes) <= finish:
        starts.append(cursor.time())
        cursor += datetime.timedelta(minutes=start_interval_minutes)
    return starts


def _existing_start_times(lesson, session_date, duration_minutes=90, start_interval_minutes=30):
    lesson_range = _parse_thing_range(lesson.thing)
    if not lesson_range:
        return []
    lesson_start, lesson_end = lesson_range
    return [
        start for start in _flexible_start_times(
            session_date, duration_minutes, start_interval_minutes,
        )
        if lesson_start <= start < lesson_end
    ]


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


def _flexible_options(
    subject, session_date, duration_minutes=90, course_filter='', start_interval_minutes=30,
):
    if subject not in FLEXIBLE_SUBJECTS:
        return []
    data = []
    wanted_course = course_filter.strip().casefold()
    for start in _flexible_start_times(
        session_date, duration_minutes, start_interval_minutes,
    ):
        end_dt = datetime.datetime.combine(session_date, start) + datetime.timedelta(minutes=duration_minutes)
        if end_dt.date() != session_date:
            continue
        end = end_dt.time()
        for room, course_name in _allowed_room_courses(subject, session_date):
            if wanted_course and course_name.strip().casefold() != wanted_course:
                continue
            has_regular_class = _has_regular_class(room, session_date, start, end)
            data.append({
                'mode': 'flexible',
                'option_key': f'flexible:{course_name}:{room.id}:{start.strftime("%H:%M")}',
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
def templates(request):
    return APIResponse(
        code=0,
        msg='Query successful',
        data=public_trial_package_templates(),
    )


@api_view(['GET'])
@authentication_classes([AdminTokenAuthtication])
def options(request):
    session_date = parse_date(request.GET.get('date', ''))
    subject = request.GET.get('subject', '')
    if not session_date or subject not in SUBJECT_COURSES:
        return APIResponse(code=1, msg='Select a valid subject and date')
    try:
        duration_minutes = int(request.GET.get('duration') or 90)
    except (TypeError, ValueError):
        return APIResponse(code=1, msg='Select a valid trial duration')
    if duration_minutes not in (60, 90, 120):
        return APIResponse(code=1, msg='Select a valid trial duration')
    try:
        start_interval_minutes = int(request.GET.get('start_interval') or 30)
    except (TypeError, ValueError):
        return APIResponse(code=1, msg='Select a valid trial start interval')
    if start_interval_minutes not in (30, 60):
        return APIResponse(code=1, msg='Select a valid trial start interval')
    course_filter = str(request.GET.get('course') or '').strip()
    if course_filter and course_filter not in SUBJECT_COURSES[subject]:
        return APIResponse(code=1, msg='Selected course does not match this trial subject')
    mode = request.GET.get('mode', 'existing')
    if mode == 'flexible':
        if subject not in FLEXIBLE_SUBJECTS:
            return APIResponse(code=1, msg='Flexible trial slots are not available for this subject')
        return APIResponse(code=0, msg='Query successful', data=_flexible_options(
            subject, session_date, duration_minutes, course_filter, start_interval_minutes,
        ))
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
        if course_filter and lesson.thing.title != course_filter:
            continue
        if not _course_allowed_for_date(
            lesson.thing.tag_id, lesson.thing.title, session_date,
        ):
            continue
        for start in _existing_start_times(
            lesson, session_date, duration_minutes, start_interval_minutes,
        ):
            end = (
                datetime.datetime.combine(session_date, start) + datetime.timedelta(minutes=duration_minutes)
            ).time()
            data.append({
                'mode': 'existing',
                'option_key': f'existing:{lesson.id}:{start.strftime("%H:%M")}',
                'lesson_id': lesson.id,
                'course': lesson.thing.title,
                'room': lesson.thing.tag.title,
                'start': start.strftime('%H:%M'),
                'end': end.strftime('%H:%M'),
                'duration': duration_minutes,
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
            'session_index': item.session_index,
            'date': item.session_date.strftime('%Y-%m-%d'),
            'course': item.course_name or (thing.title if thing else ''),
            'room': item.room.title if item.room_id else (thing.tag.title if thing and thing.tag else ''),
            'time': f'{item.starts_at.strftime("%H:%M")}-{item.ends_at.strftime("%H:%M")}',
            'duration': int((
                datetime.datetime.combine(item.session_date, item.ends_at)
                - datetime.datetime.combine(item.session_date, item.starts_at)
            ).total_seconds() // 60),
            'booking_mode': item.booking_mode,
            'teacher_confirmation_required': item.teacher_confirmation_required,
        })
    data = list(packages.values())
    for package in data:
        package['sessions'].sort(key=lambda session: session['session_index'])
        signatures = [
            (session['course'], session['duration'])
            for session in package['sessions']
        ]
        package_type = infer_trial_package_type(signatures)
        package['package_type'] = package_type
        package['package_label'] = trial_package_label(package_type)
    return APIResponse(code=0, msg='Query successful', data=data)


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
    package_type = str(request.data.get('package_type') or 'standard')
    template = TRIAL_PACKAGE_TEMPLATES.get(package_type)
    if not template:
        return APIResponse(code=1, msg='Select a valid trial package')
    sessions = request.data.get('sessions')
    expected_sessions = template['sessions']
    if not isinstance(sessions, list) or len(sessions) != len(expected_sessions):
        return APIResponse(code=1, msg='Trial sessions do not match the selected package')
    note = str(request.data.get('note') or '').strip()[:500]
    prepared = []
    for item, session_spec in zip(sessions, expected_sessions):
        session_date = parse_date(str(item.get('date') or ''))
        mode = str(item.get('mode') or 'existing')
        duration_minutes = int(session_spec['duration'])
        start_interval_minutes = int(session_spec.get('start_interval') or 30)
        requested_subject = str(item.get('subject') or session_spec['subject'])
        if session_spec.get('subject_locked') and requested_subject != session_spec['subject']:
            return APIResponse(code=1, msg='Trial subject does not match the selected package')
        if requested_subject not in SUBJECT_COURSES:
            return APIResponse(code=1, msg='Select a valid trial subject')
        required_course = str(session_spec.get('course') or '').strip()
        if mode == 'flexible':
            subject = requested_subject
            requested_course = str(item.get('course') or '').strip()
            if required_course and requested_course.casefold() != required_course.casefold():
                return APIResponse(code=1, msg='Trial course does not match the selected package')
            if not session_date:
                return APIResponse(code=1, msg='Select a valid date for the flexible trial slot')
            try:
                start = datetime.time.fromisoformat(str(item.get('start') or '').strip().zfill(5))
                room_id = int(item.get('room_id'))
            except (AttributeError, TypeError, ValueError):
                return APIResponse(code=1, msg='Selected flexible trial slot is not available')
            candidates = [
                (room, course_name)
                for room, course_name in _allowed_room_courses(subject, session_date)
                if room.id == room_id and (
                    not requested_course or course_name.casefold() == requested_course.casefold()
                )
            ]
            if len(candidates) != 1:
                return APIResponse(code=1, msg='Selected course is not allowed in this room')
            room, course_name = candidates[0]
            if subject not in FLEXIBLE_SUBJECTS or start not in _flexible_start_times(
                session_date, duration_minutes, start_interval_minutes,
            ):
                return APIResponse(code=1, msg='Selected flexible trial slot is not available')
            end_dt = datetime.datetime.combine(session_date, start) + datetime.timedelta(minutes=duration_minutes)
            if end_dt.date() != session_date:
                return APIResponse(code=1, msg='Selected flexible trial slot is not available')
            end = end_dt.time()
            prepared.append({
                'mode': 'flexible',
                'lesson': None,
                'room': room,
                'room_id': room.id,
                'course_name': course_name,
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
        if not item.get('subject') and not session_spec.get('subject_locked'):
            matching_subjects = [
                subject_name
                for subject_name, course_names in SUBJECT_COURSES.items()
                if lesson.thing.title in course_names
            ]
            if matching_subjects:
                requested_subject = matching_subjects[0]
        if lesson.thing.title not in SUBJECT_COURSES[requested_subject]:
            return APIResponse(code=1, msg='Selected class does not match the trial subject')
        if required_course and lesson.thing.title.casefold() != required_course.casefold():
            return APIResponse(code=1, msg='Selected class does not match the trial package')
        if not _course_allowed_for_date(
            lesson.thing.tag_id, lesson.thing.title, session_date,
        ):
            return APIResponse(
                code=1,
                msg=f'{lesson.thing.title} is not allowed in {lesson.thing.tag.title}',
            )
        if not any(lesson.thing.title in courses for courses in SUBJECT_COURSES.values()):
            return APIResponse(code=1, msg='This course is not in the trial package')
        if not lesson.thing.tag_id:
            return APIResponse(code=1, msg='Trial class needs a room and valid start time')
        requested_start = str(item.get('start') or '').strip()
        if requested_start:
            try:
                start = datetime.time.fromisoformat(requested_start.zfill(5))
            except ValueError:
                return APIResponse(code=1, msg='Selected trial start time is not available')
            if start not in _existing_start_times(
                lesson, session_date, duration_minutes, start_interval_minutes,
            ):
                return APIResponse(code=1, msg='Selected trial start time is not available')
            end = (
                datetime.datetime.combine(session_date, start) + datetime.timedelta(minutes=duration_minutes)
            ).time()
        else:
            available_starts = _existing_start_times(
                lesson, session_date, duration_minutes, start_interval_minutes,
            )
            if not available_starts:
                return APIResponse(code=1, msg='Trial class needs a room and valid start time')
            start = available_starts[0]
            end = (
                datetime.datetime.combine(session_date, start)
                + datetime.timedelta(minutes=duration_minutes)
            ).time()
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
            return APIResponse(
                code=1,
                msg=f'{item["room"].title} is full during this trial session',
            )
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
