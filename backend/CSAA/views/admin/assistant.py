import json
import os
import re
from datetime import date, timedelta
from urllib import error as url_error
from urllib import request as url_request

from rest_framework.decorators import api_view, authentication_classes

from CSAA.auth.authentication import AdminOrTeacherTokenAuthtication
from CSAA.handler import APIResponse
from CSAA.models import Child, ClassPass, Course, Order, RoomCoursePermission, Tag, Term, Thing
from CSAA.room_permissions import blocked_day_codes, course_allowed
from CSAA.views.admin.student import _slot_payload


DAY_ORDER = {'Mon': 0, 'Tue': 1, 'Wed': 2, 'Thu': 3, 'Fri': 4, 'Sat': 5, 'Sun': 6}
DAY_ALIASES = {
    'Mon': ('monday', 'mon', '周一', '星期一'),
    'Tue': ('tuesday', 'tue', '周二', '星期二'),
    'Wed': ('wednesday', 'wed', '周三', '星期三'),
    'Thu': ('thursday', 'thu', '周四', '星期四'),
    'Fri': ('friday', 'fri', '周五', '星期五'),
    'Sat': ('saturday', 'sat', '周六', '星期六'),
    'Sun': ('sunday', 'sun', '周日', '星期日', '星期天'),
}
AVAILABILITY_WORDS = (
    'available', 'availability', 'seat', 'space', 'spot', 'full',
    '空位', '位置', '名额', '有位', '满员', '满了',
)
REMAINING_WORDS = (
    'remaining', 'left', 'lesson', 'session', 'classes',
    '剩余', '还有', '几节', '课时', '多少课',
)


def _clean(value):
    return str(value or '').strip()


def _casefold(value):
    return _clean(value).casefold()


def _best_substring(question, values):
    normalized = _casefold(question)
    matches = [value for value in values if value and _casefold(value) in normalized]
    return max(matches, key=lambda value: len(_clean(value)), default='')


def _local_interpret(question):
    normalized = _casefold(question)
    intent = 'student_remaining' if any(word in normalized for word in REMAINING_WORDS) else 'availability'
    if any(word in normalized for word in AVAILABILITY_WORDS):
        intent = 'availability'

    students = list(Child.objects.exclude(name='').values_list('name', flat=True).distinct())
    courses = set(Course.objects.filter(active=True).values_list('title', flat=True))
    courses.update(Thing.objects.filter(status='0').exclude(title='').values_list('title', flat=True))
    rooms = list(Tag.objects.exclude(title='').values_list('title', flat=True))
    terms = list(Term.objects.exclude(title='').values_list('title', flat=True))
    day = next((code for code, aliases in DAY_ALIASES.items() if any(alias in normalized for alias in aliases)), '')
    time_match = re.search(r'(?<!\d)(\d{1,2})\s*[:：]\s*(\d{2})(?!\d)', question)

    return {
        'intent': intent,
        'student_name': _best_substring(question, students),
        'course': _best_substring(question, courses),
        'room': _best_substring(question, rooms),
        'term': _best_substring(question, terms),
        'day': day,
        'time': f'{int(time_match.group(1)):02d}:{time_match.group(2)}' if time_match else '',
    }


def _extract_json(content):
    content = _clean(content).replace('```json', '').replace('```', '')
    start, end = content.find('{'), content.rfind('}')
    if start < 0 or end < start:
        raise ValueError('AI response did not contain JSON')
    return json.loads(content[start:end + 1])


def _ai_interpret(question):
    api_key = _clean(os.environ.get('CSAA_AI_API_KEY'))
    model = _clean(os.environ.get('CSAA_AI_MODEL'))
    base_url = _clean(os.environ.get('CSAA_AI_BASE_URL', 'https://api.openai.com/v1'))
    if not api_key or not model:
        return None

    endpoint = base_url if base_url.rstrip('/').endswith('/chat/completions') else f"{base_url.rstrip('/')}/chat/completions"
    system_prompt = (
        'You classify an internal school scheduling query. Return one JSON object only. '
        'Allowed intent values are availability and student_remaining. Include these string fields: '
        'intent, student_name, course, room, term, day, time. Use Mon/Tue/Wed/Thu/Fri/Sat/Sun for day. '
        'Leave unknown fields empty. Never answer the question and never invent a value.'
    )
    payload = json.dumps({
        'model': model,
        'temperature': 0,
        'messages': [
            {'role': 'system', 'content': system_prompt},
            {'role': 'user', 'content': question},
        ],
    }).encode('utf-8')
    request = url_request.Request(
        endpoint,
        data=payload,
        headers={
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json',
        },
        method='POST',
    )
    try:
        with url_request.urlopen(request, timeout=12) as response:
            response_data = json.loads(response.read().decode('utf-8'))
        content = response_data['choices'][0]['message']['content']
        parsed = _extract_json(content)
        if parsed.get('intent') not in ('availability', 'student_remaining'):
            raise ValueError('Unsupported intent')
        return {key: _clean(parsed.get(key)) for key in (
            'intent', 'student_name', 'course', 'room', 'term', 'day', 'time'
        )}
    except (KeyError, ValueError, TypeError, json.JSONDecodeError, url_error.URLError, TimeoutError):
        return None


def interpret_question(question):
    local_result = _local_interpret(question)
    ai_question = question
    if local_result.get('student_name'):
        ai_question = re.sub(
            re.escape(local_result['student_name']), '[STUDENT]', question, flags=re.IGNORECASE,
        )
    ai_result = _ai_interpret(ai_question)
    if ai_result:
        # Database-backed names are more reliable than model spelling when they occur verbatim.
        for key in ('student_name', 'course', 'room', 'term', 'day', 'time'):
            if local_result.get(key):
                ai_result[key] = local_result[key]
        return ai_result, 'ai'
    configured = bool(_clean(os.environ.get('CSAA_AI_API_KEY')) and _clean(os.environ.get('CSAA_AI_MODEL')))
    return local_result, 'local_fallback' if configured else 'local'


def _selected_terms(term_text):
    terms = Term.objects.all()
    if term_text:
        matches = list(terms.filter(title__icontains=term_text).order_by('-expect_time', '-id'))
        return matches[:3]

    today = date.today()
    active = list(terms.filter(
        expect_time__date__lte=today,
        return_time__date__gte=today,
    ).order_by('-expect_time', '-id'))
    if active:
        return [active[0]]
    nearest = terms.filter(return_time__date__gte=today).order_by('expect_time', 'id').first()
    return [nearest] if nearest else list(terms.order_by('-return_time', '-id')[:1])


def _availability_result(filters):
    terms = _selected_terms(filters.get('term'))
    if not terms:
        return {
            'intent': 'availability',
            'answer': 'No term is configured, so class availability cannot be calculated.',
            'items': [],
        }

    things = Thing.objects.filter(status='0', tag__isnull=False, time__isnull=False)
    things = things.select_related('tag', 'time').order_by('day', 'time__time', 'tag__title', 'title', 'id')
    if filters.get('course'):
        if Thing.objects.filter(status='0', title__iexact=filters['course']).exists():
            things = things.filter(title__iexact=filters['course'])
        else:
            things = things.filter(title__icontains=filters['course'])
    if filters.get('room'):
        things = things.filter(tag__title__icontains=filters['room'])
    if filters.get('day') in DAY_ORDER:
        things = things.filter(day=filters['day'])
    if filters.get('time'):
        things = things.filter(time__time__contains=filters['time'])

    all_orders = list(Order.objects.filter(
        thing__tag__isnull=False,
        thing__time__isnull=False,
        child__isnull=False,
        status__in=[2, 6],
        trial_package_requests__isnull=True,
    ).select_related('thing__tag', 'thing__time', 'term'))
    rules = {
        (rule.room_id, rule.term_id): rule
        for rule in RoomCoursePermission.objects.filter(term__in=terms).prefetch_related('courses')
    }

    rows = []
    seen = set()
    for term in terms:
        for thing in things:
            key = (term.id, _casefold(thing.title), thing.tag_id, thing.day, thing.time_id)
            if key in seen:
                continue
            seen.add(key)
            rule = rules.get((thing.tag_id, term.id))
            if rule and thing.day in blocked_day_codes(rule):
                continue
            if not course_allowed(thing.tag_id, term, thing.title, thing.day):
                continue
            slot = _slot_payload(thing, term, orders=all_orders)
            if slot['available_seats'] is None or slot['available_seats'] <= 0:
                continue
            rows.append({
                'class_id': thing.id,
                'course': thing.title,
                'day': thing.day,
                'time': thing.time.time,
                'room': thing.tag.title,
                'available_seats': slot['available_seats'],
                'capacity': slot['capacity'],
                'enrolled_count': slot['enrolled_count'],
                'term': term.title,
            })

    def time_sort(value):
        match = re.match(r'\s*(\d{1,2}):(\d{2})', value or '')
        return int(match.group(1)) * 60 + int(match.group(2)) if match else 9999

    rows.sort(key=lambda item: (
        item['term'] or '', DAY_ORDER.get(item['day'], 9), time_sort(item['time']),
        item['room'] or '', item['course'] or '',
    ))
    total = len(rows)
    shown = rows[:40]
    filter_labels = [
        filters.get('course'), filters.get('day'), filters.get('time'),
        filters.get('room'), filters.get('term'),
    ]
    scope = ', '.join(value for value in filter_labels if value)
    if total:
        suffix = f' matching {scope}' if scope else ''
        answer = f'Found {total} class option{"s" if total != 1 else ""}{suffix} with at least one seat available.'
        if total > len(shown):
            answer += f' Showing the first {len(shown)}.'
    else:
        suffix = f' for {scope}' if scope else ''
        answer = f'No available recurring class slots were found{suffix}.'
    return {'intent': 'availability', 'answer': answer, 'items': shown}


def _student_candidates(name, question):
    students = Child.objects.select_related('parent')
    if name:
        exact = list(students.filter(name__iexact=name).order_by('id'))
        if exact:
            return exact
        contains = list(students.filter(name__icontains=name).order_by('name', 'id')[:12])
        if contains:
            return contains

    question_folded = _casefold(question)
    embedded = [student for student in students.exclude(name='') if _casefold(student.name) in question_folded]
    if embedded:
        longest = max(len(_clean(student.name)) for student in embedded)
        return [student for student in embedded if len(_clean(student.name)) == longest]
    return []


def _student_remaining_result(filters, question):
    candidates = _student_candidates(filters.get('student_name'), question)
    if not candidates:
        return {
            'intent': 'student_remaining',
            'answer': 'I could not identify the student. Include the full student name shown in the system.',
            'items': [],
        }
    if len(candidates) > 1:
        return {
            'intent': 'student_remaining',
            'answer': 'More than one student matches that name. Please include the full name or student ID.',
            'items': [{
                'student_id': student.id,
                'student_name': student.name,
                'parent': student.parent.nickname or student.parent.username if student.parent else '',
            } for student in candidates],
            'needs_clarification': True,
        }

    student = candidates[0]
    orders = Order.objects.filter(
        child=student,
        status__in=[2, 6],
        trial_package_requests__isnull=True,
    ).select_related('thing', 'thing__tag', 'thing__time', 'term').order_by(
        'term__return_time', 'thing__day', 'thing__time__time', 'id',
    )
    items = []
    total_remaining = 0
    estimated_remaining = 0

    def weekly_dates_left(order):
        if not order.thing or order.thing.day not in DAY_ORDER:
            return None
        start = order.expect_time.date() if order.expect_time else date.today()
        end_value = order.return_time or (order.term.return_time if order.term else None)
        if not end_value:
            return None
        end = end_value.date()
        start = max(start, date.today())
        if start > end:
            return 0
        first = start + timedelta(
            days=(DAY_ORDER[order.thing.day] - start.weekday()) % 7,
        )
        return 0 if first > end else ((end - first).days // 7) + 1

    for order in orders:
        remaining = int(order.num or 0)
        total_remaining += remaining
        calendar_estimate = weekly_dates_left(order)
        if remaining == 0 and calendar_estimate:
            estimated_remaining += calendar_estimate
        items.append({
            'type': 'enrollment',
            'order_id': order.id,
            'course': order.thing.title if order.thing else 'Unassigned class',
            'day': order.thing.day if order.thing else '',
            'time': order.thing.time.time if order.thing and order.thing.time else '',
            'room': order.thing.tag.title if order.thing and order.thing.tag else '',
            'term': order.term.title if order.term else '',
            'remaining_lessons': remaining,
            'calendar_estimate': calendar_estimate,
            'balance_source': 'recorded' if remaining > 0 else 'calendar_estimate',
            'start_date': order.expect_time.date().isoformat() if order.expect_time else '',
            'end_date': order.return_time.date().isoformat() if order.return_time else '',
        })

    passes = ClassPass.objects.filter(child=student, status='active').order_by('valid_until', 'id')
    for class_pass in passes:
        remaining = max(0, int(class_pass.total_sessions or 0) - int(class_pass.used_sessions or 0))
        total_remaining += remaining
        items.append({
            'type': 'class_pass',
            'class_pass_id': class_pass.id,
            'course': class_pass.title,
            'remaining_lessons': remaining,
            'start_date': class_pass.valid_from.isoformat() if class_pass.valid_from else '',
            'end_date': class_pass.valid_until.isoformat() if class_pass.valid_until else '',
        })

    if total_remaining > 0:
        answer = (
            f'{student.name} has {total_remaining} remaining lesson'
            f'{"s" if total_remaining != 1 else ""} recorded across {len(items)} active enrollment'
            f'{"s" if len(items) != 1 else ""}.'
        )
        if estimated_remaining:
            answer += f' Another {estimated_remaining} weekly class date(s) are estimated for enrollment(s) without a tracked balance.'
    elif estimated_remaining:
        answer = (
            f'{student.name} has no tracked remaining-lesson balance in the legacy order data. '
            f'The current weekly schedule has approximately {estimated_remaining} class date'
            f'{"s" if estimated_remaining != 1 else ""} remaining.'
        )
    elif items:
        answer = f'{student.name} has no recorded or scheduled lessons remaining in the active enrollment data.'
    else:
        answer = f'No active enrollment or class pass was found for {student.name}.'
    return {
        'intent': 'student_remaining',
        'answer': answer,
        'student': {'id': student.id, 'name': student.name},
        'items': items,
    }


@api_view(['POST'])
@authentication_classes([AdminOrTeacherTokenAuthtication])
def query(request):
    question = _clean(request.data.get('question'))
    if not question:
        return APIResponse(code=1, msg='Please enter a question.')
    if len(question) > 500:
        return APIResponse(code=1, msg='Question must be 500 characters or fewer.')

    filters, interpreter = interpret_question(question)
    if filters['intent'] == 'student_remaining':
        result = _student_remaining_result(filters, question)
    else:
        result = _availability_result(filters)
    result.update({
        'question': question,
        'filters': filters,
        'interpreter': interpreter,
        'ai_configured': bool(_clean(os.environ.get('CSAA_AI_API_KEY')) and _clean(os.environ.get('CSAA_AI_MODEL'))),
        'read_only': True,
    })
    return APIResponse(code=0, msg='Query completed', data=result)
