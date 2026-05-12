from django.db.models import Q
from rest_framework.decorators import api_view

from CSAA.handler import APIResponse
from CSAA.models import CourseAdjustment
from CSAA.serializers import CourseAdjustmentSerializer


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

    serializer = CourseAdjustmentSerializer(adjustments, many=True)
    return APIResponse(code=0, msg='Query successful', data=serializer.data)
