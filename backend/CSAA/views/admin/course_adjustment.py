import json
from datetime import timedelta

from django.db.models import Q
from django.utils.dateparse import parse_date
from django.utils import timezone
from rest_framework.decorators import api_view

from CSAA.course_conflicts import student_slot_conflict_on_date
from CSAA.handler import APIResponse
from CSAA.models import CourseAdjustment, Lesson, Order, Thing, User
from CSAA.serializers import CourseAdjustmentSerializer


DAY_INDEX = {
    'Mon': 0,
    'Tue': 1,
    'Wed': 2,
    'Thu': 3,
    'Fri': 4,
    'Sat': 5,
    'Sun': 6,
}


@api_view(['GET'])
def list_api(request):
    keyword = request.GET.get('keyword', '')
    status = request.GET.get('status', '')

    adjustments = CourseAdjustment.objects.select_related(
        'student',
        'parent',
        'original_order',
        'original_class',
        'original_class__time',
        'original_class__tag',
        'original_term',
        'selected_target_class',
    ).order_by('-created_time')

    if status:
        adjustments = adjustments.filter(status=status)

    if keyword:
        adjustments = adjustments.filter(
            Q(student__name__contains=keyword)
            | Q(parent__username__contains=keyword)
            | Q(parent__nickname__contains=keyword)
            | Q(parent__mobile__contains=keyword)
            | Q(original_class__title__contains=keyword)
            | Q(original_order__order_number__contains=keyword)
        )

    for adjustment in adjustments:
        if adjustment.request_type == 'makeup_class' and adjustment.status == 'makeup_available':
            adjustment.recommended_options = json.dumps(_recommend_makeup_options(adjustment, limit=2))
            adjustment.save()

    serializer = CourseAdjustmentSerializer(adjustments, many=True)
    return APIResponse(code=0, msg='Query successful', data=serializer.data)


def _date_part(value):
    if not value:
        return None
    if hasattr(value, 'date'):
        return value.date()
    return value


def _next_class_date(day, start_date, end_date):
    if day not in DAY_INDEX or not start_date or not end_date:
        return None

    days_ahead = (DAY_INDEX[day] - start_date.weekday()) % 7
    class_date = start_date + timedelta(days=days_ahead)
    if class_date <= start_date:
        class_date = class_date + timedelta(days=7)
    if class_date > end_date:
        return None
    return class_date


def _class_dates(day, start_date, end_date):
    class_date = _next_class_date(day, start_date, end_date)
    while class_date and class_date <= end_date:
        yield class_date
        class_date += timedelta(days=7)


def _eligible_term_ranges(adjustment):
    original_start = adjustment.original_lesson_date or _date_part(adjustment.original_term.expect_time)
    original_end = _date_part(adjustment.original_term.return_time)
    if not original_start or not original_end:
        return []

    ranges = [{
        'term_id': adjustment.original_term_id,
        'term_title': adjustment.original_term.title,
        'start_date': original_start,
        'end_date': original_end,
    }]

    if not adjustment.student or not adjustment.original_class:
        return ranges

    future_orders = Order.objects.filter(
        child=adjustment.student,
        status__in=[2, 6],
        term__isnull=False,
        thing__title__iexact=adjustment.original_class.title,
        term__expect_time__isnull=False,
        term__return_time__isnull=False,
        term__expect_time__gt=adjustment.original_term.return_time,
    ).select_related('term').order_by('term__expect_time', 'term_id')

    seen_terms = {adjustment.original_term_id}
    for order in future_orders:
        if order.term_id in seen_terms:
            continue
        seen_terms.add(order.term_id)
        ranges.append({
            'term_id': order.term_id,
            'term_title': order.term.title,
            'start_date': _date_part(order.term.expect_time),
            'end_date': _date_part(order.term.return_time),
        })
    return ranges


def _scheduled_count_for_slot(thing, target_date=None):
    if not thing:
        return 0

    same_slot = Thing.objects.filter(tag=thing.tag, day=thing.day, time=thing.time)
    scheduled_orders = Order.objects.filter(
        thing__in=same_slot,
        child__isnull=False,
        status__in=[2, 6],
    )
    if target_date:
        scheduled_orders = scheduled_orders.filter(
            expect_time__date__lte=target_date,
            return_time__date__gte=target_date,
        )
    scheduled_makeups = CourseAdjustment.objects.filter(
        selected_target_class__in=same_slot,
        request_type='makeup_class',
        status='completed',
    )
    if target_date:
        scheduled_makeups = scheduled_makeups.filter(selected_target_date=target_date)
    return scheduled_orders.count() + scheduled_makeups.count()


def _build_option(thing, class_date, term_range=None):
    capacity = thing.tag.seat if thing.tag else None
    enrolled_count = _scheduled_count_for_slot(thing, class_date)
    available_seats = None if capacity is None else max(int(capacity) - enrolled_count, 0)

    return {
        'class_id': thing.id,
        'class_title': thing.title,
        'date': class_date.strftime('%Y-%m-%d') if class_date else None,
        'day': thing.day,
        'time': thing.time.time if thing.time else None,
        'room': thing.tag.title if thing.tag else None,
        'capacity': capacity,
        'enrolled_count': enrolled_count,
        'available_seats': available_seats,
        'term_id': term_range.get('term_id') if term_range else None,
        'term_title': term_range.get('term_title') if term_range else None,
    }


def _student_has_slot_conflict(student, thing, class_date):
    return bool(student_slot_conflict_on_date(student, thing, class_date))


def _recommend_makeup_options(adjustment, limit=2):
    if not adjustment.original_class or not adjustment.original_term:
        return []

    term_ranges = _eligible_term_ranges(adjustment)
    if not term_ranges:
        return []

    candidates = Thing.objects.filter(
        title__iexact=adjustment.original_class.title,
        status='0',
        day__isnull=False,
        time__isnull=False,
        tag__isnull=False,
    ).select_related('time', 'tag').order_by('day', 'time__time', 'tag__title', 'id')

    options = []
    seen_options = set()
    for term_range in term_ranges:
        for thing in candidates:
            for class_date in _class_dates(
                thing.day,
                term_range['start_date'],
                term_range['end_date'],
            ):
                option_key = (thing.id, class_date)
                if option_key in seen_options:
                    continue
                if thing.id == adjustment.original_class_id and class_date == adjustment.original_lesson_date:
                    continue
                if _student_has_slot_conflict(adjustment.student, thing, class_date):
                    continue
                option = _build_option(thing, class_date, term_range)
                if option['available_seats'] is not None and option['available_seats'] <= 0:
                    continue
                seen_options.add(option_key)
                options.append(option)
                if limit and len(options) >= limit:
                    return options

    return options


def _all_saved_recommendations(adjustment):
    recommendations = []
    if adjustment.recommended_options:
        try:
            recommendations.extend(json.loads(adjustment.recommended_options))
        except (TypeError, ValueError):
            pass
    if adjustment.admin_extra_recommendation:
        try:
            recommendations.append(json.loads(adjustment.admin_extra_recommendation))
        except (TypeError, ValueError):
            pass
    return recommendations


def _find_saved_recommendation(adjustment, class_id, class_date):
    for option in _all_saved_recommendations(adjustment):
        if str(option.get('class_id')) == str(class_id) and option.get('date') == class_date:
            return option
    return None


@api_view(['POST'])
def review_api(request):
    adjustment_id = request.data.get('id') or request.GET.get('id')
    action = request.data.get('action') or request.GET.get('action')
    admin_note = request.data.get('admin_note') or request.GET.get('admin_note') or ''
    admin_user_id = request.data.get('admin_user_id') or request.GET.get('admin_user_id')

    if action not in ['approve', 'reject']:
        return APIResponse(code=1, msg='Action must be approve or reject')

    try:
        adjustment = CourseAdjustment.objects.select_related(
            'student',
            'parent',
            'original_order',
            'original_class',
            'original_term',
        ).get(id=adjustment_id)
    except CourseAdjustment.DoesNotExist:
        return APIResponse(code=1, msg='Adjustment request does not exist')

    if adjustment.status != 'pending':
        return APIResponse(code=1, msg='Only pending requests can be reviewed')

    admin_user = None
    if admin_user_id:
        admin_user = User.objects.filter(id=admin_user_id).first()

    if action == 'reject':
        adjustment.status = 'rejected'
        adjustment.admin_note = admin_note
        adjustment.approved_by = admin_user
        adjustment.approved_time = timezone.now()
        adjustment.save()
        serializer = CourseAdjustmentSerializer(adjustment)
        return APIResponse(code=0, msg='Request rejected', data=serializer.data)

    adjustment.status = 'approved'
    adjustment.admin_note = admin_note
    adjustment.approved_by = admin_user
    adjustment.approved_time = timezone.now()
    adjustment.save()

    makeup_record = None
    if adjustment.request_type == 'cancel_class':
        options = _recommend_makeup_options(adjustment, limit=2)
        makeup_record, _ = CourseAdjustment.objects.get_or_create(
            source_adjustment=adjustment,
            request_type='makeup_class',
            defaults={
                'student': adjustment.student,
                'parent': adjustment.parent,
                'original_order': adjustment.original_order,
                'original_class': adjustment.original_class,
                'original_lesson_date': adjustment.original_lesson_date,
                'original_day': adjustment.original_day,
                'original_time': adjustment.original_time,
                'original_term': adjustment.original_term,
                'request_reason': 'Makeup eligibility generated after cancel request approval.',
                'request_source': 'admin',
                'status': 'makeup_available',
                'recommended_options': json.dumps(options),
                'admin_note': admin_note,
                'approved_by': admin_user,
                'approved_time': timezone.now(),
            },
        )
        if makeup_record.recommended_options in [None, '']:
            makeup_record.recommended_options = json.dumps(options)
            makeup_record.save()

    serializer = CourseAdjustmentSerializer(adjustment)
    data = serializer.data
    if makeup_record:
        data['makeup_record'] = CourseAdjustmentSerializer(makeup_record).data
    return APIResponse(code=0, msg='Request approved', data=data)


@api_view(['GET'])
def recommendation_options_api(request):
    adjustment_id = request.GET.get('id')
    try:
        adjustment = CourseAdjustment.objects.select_related(
            'student',
            'original_class',
            'original_term',
        ).get(id=adjustment_id)
    except CourseAdjustment.DoesNotExist:
        return APIResponse(code=1, msg='Makeup eligibility does not exist')

    options = _recommend_makeup_options(adjustment, limit=0)
    return APIResponse(code=0, msg='Query successful', data=options)


@api_view(['POST'])
def add_extra_recommendation_api(request):
    adjustment_id = request.data.get('id') or request.GET.get('id')
    class_id = request.data.get('class_id') or request.GET.get('class_id')
    class_date = request.data.get('date') or request.GET.get('date')

    try:
        adjustment = CourseAdjustment.objects.select_related(
            'original_class',
            'original_term',
        ).get(id=adjustment_id, request_type='makeup_class')
        thing = Thing.objects.select_related('time', 'tag').get(id=class_id)
    except CourseAdjustment.DoesNotExist:
        return APIResponse(code=1, msg='Makeup eligibility does not exist')
    except Thing.DoesNotExist:
        return APIResponse(code=1, msg='Class option does not exist')

    options = _recommend_makeup_options(adjustment, limit=0)
    selected = None
    for option in options:
        if str(option['class_id']) == str(class_id) and option['date'] == class_date:
            selected = option
            break

    if not selected:
        return APIResponse(code=1, msg='This option does not match class, term, or capacity rules')

    adjustment.admin_extra_recommendation = json.dumps(selected)
    adjustment.save()

    serializer = CourseAdjustmentSerializer(adjustment)
    return APIResponse(code=0, msg='Extra recommendation saved', data=serializer.data)


@api_view(['POST'])
def confirm_makeup_schedule_api(request):
    adjustment_id = request.data.get('id') or request.GET.get('id')
    class_id = request.data.get('class_id') or request.GET.get('class_id')
    class_date = request.data.get('date') or request.GET.get('date')
    admin_note = request.data.get('admin_note') or request.GET.get('admin_note') or ''

    try:
        adjustment = CourseAdjustment.objects.select_related(
            'student',
            'parent',
            'original_class',
            'original_term',
        ).get(id=adjustment_id, request_type='makeup_class')
        thing = Thing.objects.select_related('time', 'tag').get(id=class_id)
    except CourseAdjustment.DoesNotExist:
        return APIResponse(code=1, msg='Makeup eligibility does not exist')
    except Thing.DoesNotExist:
        return APIResponse(code=1, msg='Class option does not exist')

    if adjustment.status != 'makeup_available':
        return APIResponse(code=1, msg='Only available makeup eligibility can be scheduled')

    selected = _find_saved_recommendation(adjustment, class_id, class_date)
    if not selected:
        return APIResponse(code=1, msg='Please choose one of the recommended makeup options')

    target_date = parse_date(class_date)
    if not target_date:
        return APIResponse(code=1, msg='Invalid makeup date')

    current_recommendation = next(
        (
            option
            for option in _recommend_makeup_options(adjustment, limit=0)
            if str(option.get('class_id')) == str(class_id)
            and option.get('date') == class_date
        ),
        None,
    )
    if not current_recommendation:
        return APIResponse(
            code=1,
            msg=(
                'This makeup option is no longer eligible. '
                'Check the student schedule, term enrollment, and capacity.'
            ),
        )

    current_option = _build_option(thing, target_date)
    if current_option['available_seats'] is not None and current_option['available_seats'] <= 0:
        return APIResponse(code=1, msg='Selected class is full')
    conflict = student_slot_conflict_on_date(adjustment.student, thing, target_date)
    if conflict:
        return APIResponse(code=1, msg=conflict)

    lesson = Lesson.objects.get_or_create(thing=thing)[0]
    if adjustment.student:
        lesson.reschedule_students.add(adjustment.student)

    adjustment.selected_target_class = thing
    adjustment.selected_target_date = target_date
    adjustment.selected_target_day = thing.day
    adjustment.selected_target_time = thing.time.time if thing.time else None
    adjustment.selected_target_room = thing.tag.title if thing.tag else None
    adjustment.status = 'completed'
    if admin_note:
        adjustment.admin_note = admin_note
    adjustment.save()

    serializer = CourseAdjustmentSerializer(adjustment)
    return APIResponse(code=0, msg='Makeup class scheduled', data=serializer.data)
