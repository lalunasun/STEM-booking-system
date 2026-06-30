import datetime

from django.db import transaction
from django.db.models import Q
from django.utils import timezone
from django.utils.dateparse import parse_date
from rest_framework.decorators import api_view, authentication_classes

from CSAA.auth.authentication import AdminTokenAuthtication
from CSAA.handler import APIResponse
from CSAA.models import Child, ClassPass, ClassPassBooking, Lesson, Order, Thing
from CSAA.serializers import ClassPassBookingSerializer, ClassPassSerializer


def _base_pass_query():
    return ClassPass.objects.select_related('parent', 'child', 'created_by').order_by('-updated_time', '-id')


def _base_booking_query():
    return ClassPassBooking.objects.select_related(
        'class_pass',
        'parent',
        'child',
        'requested_class',
        'requested_class__time',
        'requested_class__tag',
        'target_lesson',
        'reviewed_by',
        'completed_by',
    ).order_by('-created_time', '-id')


def _remaining(class_pass):
    return max(0, int(class_pass.total_sessions or 0) - int(class_pass.used_sessions or 0))


def _lesson_for_thing(thing):
    return Lesson.objects.filter(thing=thing).first()


def _parse_bool(value):
    return str(value).lower() in ['1', 'true', 'yes', 'on']


def _active_room_count(thing, lesson_date, exclude_booking_id=None):
    if not thing or not thing.tag or not thing.day or not thing.time:
        return 0

    same_room_things = Thing.objects.filter(tag=thing.tag, day=thing.day, time=thing.time)
    fixed_orders = Order.objects.filter(
        thing__in=same_room_things,
        child__isnull=False,
        status__in=[2, 6],
        trial_package_requests__isnull=True,
        expect_time__date__lte=lesson_date,
        return_time__date__gte=lesson_date,
    ).count()

    approved_bookings = ClassPassBooking.objects.filter(
        requested_class__in=same_room_things,
        requested_date=lesson_date,
        status__in=['approved', 'completed'],
    )
    if exclude_booking_id:
        approved_bookings = approved_bookings.exclude(id=exclude_booking_id)

    return fixed_orders + approved_bookings.count()


@api_view(['GET'])
@authentication_classes([AdminTokenAuthtication])
def pass_list(request):
    passes = _base_pass_query()
    parent_id = request.GET.get('parent_id')
    child_id = request.GET.get('child_id')
    status = request.GET.get('status')
    keyword = str(request.GET.get('keyword') or '').strip()
    if parent_id:
        passes = passes.filter(parent_id=parent_id)
    if child_id:
        passes = passes.filter(child_id=child_id)
    if status:
        passes = passes.filter(status=status)
    if keyword:
        filters = (
            Q(parent__username__icontains=keyword)
            | Q(parent__nickname__icontains=keyword)
            | Q(parent__mobile__icontains=keyword)
            | Q(child__name__icontains=keyword)
        )
        if keyword.isdigit():
            filters |= Q(parent_id=int(keyword)) | Q(child_id=int(keyword)) | Q(id=int(keyword))
        passes = passes.filter(filters)
    return APIResponse(code=0, msg='Success', data=ClassPassSerializer(passes, many=True).data)


@api_view(['POST'])
@authentication_classes([AdminTokenAuthtication])
def pass_create(request):
    data = request.data
    try:
        child = Child.objects.select_related('parent').get(pk=data.get('child_id') or data.get('child'))
    except (Child.DoesNotExist, TypeError, ValueError):
        return APIResponse(code=1, msg='Child does not exist')

    if not child.parent:
        return APIResponse(code=1, msg='Child has no parent')

    total_sessions = int(data.get('total_sessions') or 0)
    if total_sessions <= 0:
        return APIResponse(code=1, msg='Total sessions must be greater than 0')

    valid_from = parse_date(str(data.get('valid_from') or '')) if data.get('valid_from') else None
    valid_until = parse_date(str(data.get('valid_until') or '')) if data.get('valid_until') else None
    if valid_from and valid_until and valid_until < valid_from:
        return APIResponse(code=1, msg='Valid until cannot be before valid from')

    class_pass = ClassPass.objects.create(
        parent=child.parent,
        child=child,
        title=str(data.get('title') or 'Class Pass').strip() or 'Class Pass',
        total_sessions=total_sessions,
        used_sessions=int(data.get('used_sessions') or 0),
        valid_from=valid_from,
        valid_until=valid_until,
        status=data.get('status') or 'active',
        note=str(data.get('note') or '').strip(),
        created_by=request.user,
    )
    return APIResponse(code=0, msg='Class pass created', data=ClassPassSerializer(class_pass).data)


@api_view(['POST'])
@authentication_classes([AdminTokenAuthtication])
def pass_update(request):
    try:
        class_pass = ClassPass.objects.get(pk=request.GET.get('id') or request.data.get('id'))
    except (ClassPass.DoesNotExist, TypeError, ValueError):
        return APIResponse(code=1, msg='Class pass does not exist')

    data = request.data
    if data.get('title') is not None:
        class_pass.title = str(data.get('title') or '').strip() or 'Class Pass'
    if data.get('total_sessions') is not None:
        total_sessions = int(data.get('total_sessions') or 0)
        if total_sessions < class_pass.used_sessions:
            return APIResponse(code=1, msg='Total sessions cannot be less than used sessions')
        class_pass.total_sessions = total_sessions
    if data.get('used_sessions') is not None:
        used_sessions = int(data.get('used_sessions') or 0)
        if used_sessions < 0 or used_sessions > class_pass.total_sessions:
            return APIResponse(code=1, msg='Used sessions is invalid')
        class_pass.used_sessions = used_sessions
    if data.get('valid_from') is not None:
        class_pass.valid_from = parse_date(str(data.get('valid_from') or '')) if data.get('valid_from') else None
    if data.get('valid_until') is not None:
        class_pass.valid_until = parse_date(str(data.get('valid_until') or '')) if data.get('valid_until') else None
    if class_pass.valid_from and class_pass.valid_until and class_pass.valid_until < class_pass.valid_from:
        return APIResponse(code=1, msg='Valid until cannot be before valid from')
    if data.get('status') is not None:
        class_pass.status = data.get('status')
    if data.get('note') is not None:
        class_pass.note = str(data.get('note') or '').strip()
    class_pass.save()
    return APIResponse(code=0, msg='Class pass updated', data=ClassPassSerializer(class_pass).data)


@api_view(['GET'])
@authentication_classes([AdminTokenAuthtication])
def booking_list(request):
    bookings = _base_booking_query()
    status = request.GET.get('status')
    parent_id = request.GET.get('parent_id')
    child_id = request.GET.get('child_id')
    keyword = str(request.GET.get('keyword') or '').strip()
    if status:
        bookings = bookings.filter(status=status)
    if parent_id:
        bookings = bookings.filter(parent_id=parent_id)
    if child_id:
        bookings = bookings.filter(child_id=child_id)
    if keyword:
        filters = (
            Q(parent__username__icontains=keyword)
            | Q(parent__nickname__icontains=keyword)
            | Q(parent__mobile__icontains=keyword)
            | Q(child__name__icontains=keyword)
            | Q(requested_class__title__icontains=keyword)
        )
        if keyword.isdigit():
            filters |= Q(parent_id=int(keyword)) | Q(child_id=int(keyword)) | Q(id=int(keyword))
        bookings = bookings.filter(filters)
    return APIResponse(code=0, msg='Success', data=ClassPassBookingSerializer(bookings, many=True).data)


@api_view(['POST'])
@authentication_classes([AdminTokenAuthtication])
def booking_review(request):
    try:
        booking = _base_booking_query().get(pk=request.data.get('id'))
    except (ClassPassBooking.DoesNotExist, TypeError, ValueError):
        return APIResponse(code=1, msg='Booking does not exist')

    action = request.data.get('action')
    admin_note = str(request.data.get('admin_note') or '').strip()
    if action not in ['approve', 'reject', 'cancel']:
        return APIResponse(code=1, msg='Review action is invalid')

    if action == 'approve':
        if booking.status not in ['pending', 'approved']:
            return APIResponse(code=1, msg='Only pending bookings can be approved')
        class_pass = booking.class_pass
        today = datetime.date.today()
        if class_pass.status != 'active':
            return APIResponse(code=1, msg='Class pass is not active')
        if class_pass.valid_from and booking.requested_date < class_pass.valid_from:
            return APIResponse(code=1, msg='Requested date is before pass valid date')
        if class_pass.valid_until and booking.requested_date > class_pass.valid_until:
            return APIResponse(code=1, msg='Requested date is after pass expiry date')
        if booking.requested_date < today:
            return APIResponse(code=1, msg='Cannot approve a past class pass booking')
        if _remaining(class_pass) <= 0:
            return APIResponse(code=1, msg='No remaining sessions on this class pass')
        thing = booking.requested_class
        if not thing:
            return APIResponse(code=1, msg='Requested class is missing')
        if thing.day:
            expected_day = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'][booking.requested_date.weekday()]
            if thing.day.lower() != expected_day.lower():
                return APIResponse(code=1, msg=f'This class meets on {thing.day}, not {expected_day}')
        if thing.tag and thing.tag.seat is not None:
            if _active_room_count(thing, booking.requested_date, exclude_booking_id=booking.id) >= int(thing.tag.seat):
                return APIResponse(code=1, msg='This room/time is full on the requested date')
        lesson = _lesson_for_thing(thing)
        if not lesson:
            return APIResponse(code=1, msg='Lesson does not exist for this class')
        booking.target_lesson = lesson
        booking.status = 'approved'
    elif action == 'reject':
        booking.status = 'rejected'
    else:
        booking.status = 'canceled'

    booking.admin_note = admin_note
    booking.reviewed_by = request.user
    booking.reviewed_time = timezone.now()
    booking.save()
    return APIResponse(code=0, msg='Booking reviewed', data=ClassPassBookingSerializer(booking).data)


@api_view(['POST'])
@authentication_classes([AdminTokenAuthtication])
def booking_complete(request):
    try:
        booking = ClassPassBooking.objects.select_related('class_pass').get(pk=request.data.get('id'))
    except (ClassPassBooking.DoesNotExist, TypeError, ValueError):
        return APIResponse(code=1, msg='Booking does not exist')

    if booking.status != 'approved':
        return APIResponse(code=1, msg='Only approved bookings can be completed')

    deduct = _parse_bool(request.data.get('deduct', 'true'))
    with transaction.atomic():
        class_pass = ClassPass.objects.select_for_update().get(pk=booking.class_pass_id)
        if deduct:
            if _remaining(class_pass) <= 0:
                return APIResponse(code=1, msg='No remaining sessions on this class pass')
            class_pass.used_sessions += 1
            class_pass.save(update_fields=['used_sessions', 'updated_time'])
        booking.status = 'completed'
        booking.completed_by = request.user
        booking.completed_time = timezone.now()
        booking.save(update_fields=['status', 'completed_by', 'completed_time', 'updated_time'])

    booking = _base_booking_query().get(pk=booking.id)
    return APIResponse(code=0, msg='Booking completed', data=ClassPassBookingSerializer(booking).data)
