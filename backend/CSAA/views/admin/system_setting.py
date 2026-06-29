import json

from rest_framework.decorators import api_view, authentication_classes

from CSAA.auth.authentication import AdminOrTeacherTokenAuthtication, AdminTokenAuthtication
from CSAA.handler import APIResponse
from CSAA.models import SystemSetting
from CSAA.serializers import SystemSettingSerializer


DEFAULT_STAFF_ANNOUNCEMENT = 'Please review your classroom assignment and student changes before the first lesson.'
STAFF_ANNOUNCEMENT_KEY = 'staff_announcement'
TEACHER_ASSIGNMENTS_KEY = 'teacher_assignments'


def _request_user(request):
    return getattr(request, 'user', None)


@api_view(['GET'])
@authentication_classes([AdminOrTeacherTokenAuthtication])
def staff_announcement(request):
    setting = SystemSetting.objects.filter(key=STAFF_ANNOUNCEMENT_KEY).first()
    if not setting:
        return APIResponse(
            code=0,
            msg='Query successful',
            data={
                'key': STAFF_ANNOUNCEMENT_KEY,
                'value': DEFAULT_STAFF_ANNOUNCEMENT,
            },
        )

    serializer = SystemSettingSerializer(setting)
    return APIResponse(code=0, msg='Query successful', data=serializer.data)


@api_view(['POST'])
@authentication_classes([AdminTokenAuthtication])
def save_staff_announcement(request):
    value = (request.data.get('value') or '').strip()
    if len(value) > 500:
        return APIResponse(code=1, msg='Announcement must be 500 characters or fewer')

    if not value:
        value = DEFAULT_STAFF_ANNOUNCEMENT

    setting, _ = SystemSetting.objects.update_or_create(
        key=STAFF_ANNOUNCEMENT_KEY,
        defaults={
            'value': value,
            'updated_by': _request_user(request),
        },
    )
    serializer = SystemSettingSerializer(setting)
    return APIResponse(code=0, msg='Announcement saved', data=serializer.data)


@api_view(['GET'])
@authentication_classes([AdminOrTeacherTokenAuthtication])
def teacher_assignments(request):
    setting = SystemSetting.objects.filter(key=TEACHER_ASSIGNMENTS_KEY).first()
    value = {}
    if setting and setting.value:
        try:
            value = json.loads(setting.value)
        except json.JSONDecodeError:
            value = {}

    return APIResponse(
        code=0,
        msg='Query successful',
        data={
            'key': TEACHER_ASSIGNMENTS_KEY,
            'value': value,
        },
    )


@api_view(['POST'])
@authentication_classes([AdminTokenAuthtication])
def save_teacher_assignments(request):
    raw_value = request.data.get('value') or '{}'
    if isinstance(raw_value, str):
        try:
            value = json.loads(raw_value)
        except json.JSONDecodeError:
            return APIResponse(code=1, msg='Teacher assignment data is invalid')
    else:
        value = raw_value

    if not isinstance(value, dict):
        return APIResponse(code=1, msg='Teacher assignment data is invalid')

    cleaned = {}
    for room_id, teacher_name in value.items():
        name = str(teacher_name or '').strip()
        if len(name) > 80:
            return APIResponse(code=1, msg='Teacher name must be 80 characters or fewer')
        if name:
            cleaned[str(room_id)] = name

    setting, _ = SystemSetting.objects.update_or_create(
        key=TEACHER_ASSIGNMENTS_KEY,
        defaults={
            'value': json.dumps(cleaned),
            'updated_by': _request_user(request),
        },
    )
    return APIResponse(
        code=0,
        msg='Teacher assignments saved',
        data={
            'key': setting.key,
            'value': cleaned,
            'updated_time': setting.updated_time,
        },
    )
