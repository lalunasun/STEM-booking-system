from rest_framework.decorators import api_view

from CSAA.handler import APIResponse
from CSAA.models import OpLog
from CSAA.serializers import OpLogSerializer


# 操作日志列表
@api_view(['GET'])
def list_api(request):
    if request.method == 'GET':
        opLogs = OpLog.objects.all().order_by('-re_time')[:100]
        serializer = OpLogSerializer(opLogs, many=True)
        return APIResponse(code=0, msg='查询成功', data=serializer.data)
