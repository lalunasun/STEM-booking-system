from rest_framework.decorators import api_view

from CSAA.handler import APIResponse
from CSAA.models import Ad
from CSAA.serializers import AdSerializer


# 获取标签列表
@api_view(['GET'])
def list_api(request):
    if request.method == 'GET':
        ads = Ad.objects.all().order_by('-create_time')
        serializer = AdSerializer(ads, many=True)
        print(serializer.data)
        return APIResponse(code=0, msg='查询成功', data=serializer.data)
