import datetime

from django.utils.dateparse import parse_date
from rest_framework.decorators import api_view, authentication_classes

from CSAA.auth.authentication import TokenAuthtication
from CSAA.handler import APIResponse
from CSAA.models import Child, ClassPass, ClassPassBooking, Thing, User
from CSAA.serializers import ClassPassBookingSerializer, ClassPassSerializer


def _token_user(request):
    token = request.META.get("HTTP_TOKEN", "")
    if not token:
        return None
    return User.objects.filter(token=token).first()


def _remaining(class_pass):
    return max(0, int(class_pass.total_sessions or 0) - int(class_pass.used_sessions or 0))


def _pass_query(user):
    return ClassPass.objects.filter(parent=user).select_related('parent', 'child').order_by('-updated_time', '-id')


def _booking_query(user):
    return ClassPassBooking.objects.filter(parent=user).select_related(
        'class_pass',
        'parent',
        'child',
        'requested_class',
        'requested_class__time',
        'requested_class__tag',
        'target_lesson',
    ).order_by('-created_time', '-id')


@api_view(['GET'])
@authentication_classes([TokenAuthtication])
def pass_list(request):
    user = _token_user(request)
    if not user:
        return APIResponse(code=1, msg='User authentication failed')

    passes = _pass_query(user)
    child_id = request.GET.get('child_id')
    active_only = str(request.GET.get('active_only', '')).lower() in ['1', 'true', 'yes']
    if child_id:
        passes = passes.filter(child_id=child_id)
    if active_only:
        today = datetime.date.today()
        passes = passes.filter(status='active', total_sessions__gt=0).exclude(valid_until__lt=today)
    return APIResponse(code=0, msg='Success', data=ClassPassSerializer(passes, many=True).data)


@api_view(['GET'])
@authentication_classes([TokenAuthtication])
def booking_list(request):
    user = _token_user(request)
    if not user:
        return APIResponse(code=1, msg='User authentication failed')

    bookings = _booking_query(user)
    child_id = request.GET.get('child_id')
    if child_id:
        bookings = bookings.filter(child_id=child_id)
    return APIResponse(code=0, msg='Success', data=ClassPassBookingSerializer(bookings, many=True).data)


@api_view(['POST'])
@authentication_classes([TokenAuthtication])
def booking_create(request):
    user = _token_user(request)
    if not user:
        return APIResponse(code=1, msg='User authentication failed')
    if not user.allow_class_pass:
        return APIResponse(code=1, msg='Class pass booking is not enabled for this account')

    try:
        class_pass = ClassPass.objects.select_related('child', 'parent').get(
            pk=request.data.get('class_pass_id'),
            parent=user,
        )
    except (ClassPass.DoesNotExist, TypeError, ValueError):
        return APIResponse(code=1, msg='Class pass does not exist')

    if class_pass.status != 'active':
        return APIResponse(code=1, msg='Class pass is not active')
    if _remaining(class_pass) <= 0:
        return APIResponse(code=1, msg='No remaining sessions on this class pass')

    requested_date = parse_date(str(request.data.get('requested_date') or ''))
    if not requested_date:
        return APIResponse(code=1, msg='Please select a requested date')
    today = datetime.date.today()
    if requested_date < today:
        return APIResponse(code=1, msg='Requested date cannot be in the past')
    if class_pass.valid_from and requested_date < class_pass.valid_from:
        return APIResponse(code=1, msg='Requested date is before pass valid date')
    if class_pass.valid_until and requested_date > class_pass.valid_until:
        return APIResponse(code=1, msg='Requested date is after pass expiry date')

    try:
        requested_class = Thing.objects.select_related('time', 'tag').get(pk=request.data.get('requested_class_id'))
    except (Thing.DoesNotExist, TypeError, ValueError):
        return APIResponse(code=1, msg='Requested class does not exist')

    if requested_class.day:
        expected_day = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'][requested_date.weekday()]
        if requested_class.day.lower() != expected_day.lower():
            return APIResponse(code=1, msg=f'This class meets on {requested_class.day}, not {expected_day}')

    existing = ClassPassBooking.objects.filter(
        class_pass=class_pass,
        requested_class=requested_class,
        requested_date=requested_date,
        status__in=['pending', 'approved'],
    ).first()
    if existing:
        return APIResponse(code=0, msg='Class pass booking already exists', data=ClassPassBookingSerializer(existing).data)

    booking = ClassPassBooking.objects.create(
        class_pass=class_pass,
        parent=user,
        child=class_pass.child,
        requested_class=requested_class,
        requested_date=requested_date,
        parent_note=str(request.data.get('parent_note') or '').strip(),
        status='pending',
    )
    return APIResponse(code=0, msg='Class pass booking submitted', data=ClassPassBookingSerializer(booking).data)


@api_view(['POST'])
@authentication_classes([TokenAuthtication])
def booking_cancel(request):
    user = _token_user(request)
    if not user:
        return APIResponse(code=1, msg='User authentication failed')
    try:
        booking = ClassPassBooking.objects.get(pk=request.data.get('id'), parent=user)
    except (ClassPassBooking.DoesNotExist, TypeError, ValueError):
        return APIResponse(code=1, msg='Booking does not exist')
    if booking.status not in ['pending', 'approved']:
        return APIResponse(code=1, msg='Only pending or approved bookings can be canceled')
    booking.status = 'canceled'
    booking.parent_note = str(request.data.get('parent_note') or booking.parent_note or '').strip()
    booking.save(update_fields=['status', 'parent_note', 'updated_time'])
    return APIResponse(code=0, msg='Booking canceled', data=ClassPassBookingSerializer(booking).data)
