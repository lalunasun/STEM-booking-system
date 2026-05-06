from rest_framework.decorators import api_view

from CSAA.handler import APIResponse
from CSAA.models import Tag
from CSAA.serializers import TagSerializer


# 获取标签列表
@api_view(['GET'])
def list_api(request):
    if request.method == 'GET':
        tags = Tag.objects.all().order_by('-create_time')
        serializer = TagSerializer(tags, many=True)
        print(serializer.data)
        return APIResponse(code=0, msg='查询成功', data=serializer.data)
