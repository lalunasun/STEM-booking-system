from rest_framework.decorators import api_view

from CSAA.handler import APIResponse
from CSAA.models import Notice
from CSAA.serializers import NoticeSerializer


# 消息列表
@api_view(['GET'])
def list_api(request):
    if request.method == 'GET':
        notices = Notice.objects.all().order_by('-create_time')
        serializer = NoticeSerializer(notices, many=True)
        return APIResponse(code=0, msg='查询成功', data=serializer.data)

