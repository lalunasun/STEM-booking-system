from rest_framework.decorators import api_view

from CSAA.handler import APIResponse
from CSAA.models import Classification
from CSAA.serializers import ClassificationSerializer


# 分类列表
@api_view(['GET'])
def list_api(request):
    if request.method == 'GET':
        classifications = Classification.objects.all().order_by('-create_time')
        serializer = ClassificationSerializer(classifications, many=True)
        return APIResponse(code=0, msg='查询成功', data=serializer.data)





