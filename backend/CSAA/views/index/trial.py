from rest_framework.decorators import api_view, authentication_classes

from CSAA import utils
from CSAA.auth.authentication import TokenAuthtication
from CSAA.course_conflicts import selected_slot_conflict, student_slot_conflict
from CSAA.handler import APIResponse
from CSAA.models import Child, Order, Thing, TrialRequest, User
from CSAA.serializers import TrialRequestSerializer


def _normalize(value):
    return str(value or '').strip().lower()


def _category_is(thing, category):
    return _normalize(thing.classification.title if thing.classification else '') == _normalize(category)


def _active_occupancy(thing):
    if not thing.tag or not thing.time or not thing.day:
        return Order.objects.filter(
            thing=thing,
            child__isnull=False,
            status__in=[2, 6],
            trial_package_requests__isnull=True,
        ).count()

    same_room_things = Thing.objects.filter(tag=thing.tag, day=thing.day, time=thing.time)
    return Order.objects.filter(
        thing__in=same_room_things,
        child__isnull=False,
        status__in=[2, 6],
        trial_package_requests__isnull=True,
    ).count()


def _validate_available_slot(thing, expected_category):
    if not _category_is(thing, expected_category):
        return False, f'{expected_category} trial slot does not match the selected category'

    if str(thing.status) == '1':
        return False, f'{thing.title} is closed'

    if thing.tag and thing.tag.seat is not None and _active_occupancy(thing) >= int(thing.tag.seat):
        return False, f'{thing.title} is full'

    return True, ''


def _create_trial_package_order(parent, child, primary_thing):
    return Order.objects.create(
        order_number=str(utils.get_timestamp()),
        user=parent,
        thing=primary_thing,
        count=1,
        num=2,
        child=child,
        amount='98',
        status=1,
        receiver_phone=parent.mobile,
        remark='Trial Package',
    )


@api_view(['POST'])
@authentication_classes([TokenAuthtication])
def create(request):
    data = request.data.copy()
    parent_id = data.get('parent') or data.get('user')
    child_id = data.get('child')
    robotics_id = data.get('robotics_class')
    coding_id = data.get('coding_class')

    if not parent_id or not child_id or not robotics_id or not coding_id:
        return APIResponse(
            code=1,
            msg='Please select one Robotics and one Coding trial',
        )

    try:
        parent = User.objects.get(pk=parent_id)
        child = Child.objects.get(pk=child_id, parent=parent)
        robotics_class = Thing.objects.get(pk=robotics_id)
        coding_class = Thing.objects.get(pk=coding_id)
    except (User.DoesNotExist, Child.DoesNotExist, Thing.DoesNotExist):
        return APIResponse(code=1, msg='Trial request data is invalid')

    for thing, category in (
        (robotics_class, 'Robotics'),
        (coding_class, 'Coding'),
    ):
        ok, msg = _validate_available_slot(thing, category)
        if not ok:
            return APIResponse(code=1, msg=msg)

    selected_things = [robotics_class, coding_class]
    conflict = selected_slot_conflict(selected_things)
    if conflict:
        return APIResponse(code=1, msg=conflict)

    for thing in selected_things:
        conflict = student_slot_conflict(child, thing)
        if conflict:
            return APIResponse(code=1, msg=conflict)

    package_order = _create_trial_package_order(parent, child, robotics_class)

    trial_request = TrialRequest.objects.create(
        parent=parent,
        child=child,
        robotics_class=robotics_class,
        coding_class=coding_class,
        math_class=None,
        package_order=package_order,
        parent_note=data.get('parent_note') or '',
        status='pending',
    )
    serializer = TrialRequestSerializer(trial_request)
    return APIResponse(code=0, msg='Trial request submitted', data=serializer.data)
