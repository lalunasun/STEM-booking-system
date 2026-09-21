from rest_framework.decorators import api_view, authentication_classes

from CSAA.auth.authentication import AdminTokenAuthtication
from CSAA.handler import APIResponse
from CSAA.models import OpLog
from CSAA.serializers import OpLogSerializer


# 操作日志列表
@api_view(['GET'])
@authentication_classes([AdminTokenAuthtication])
def list_api(request):
    if request.method == 'GET':
        opLogs = OpLog.objects.all().order_by('-re_time')[:100]
        serializer = OpLogSerializer(opLogs, many=True)
        return APIResponse(code=0, msg='查询成功', data=serializer.data)
