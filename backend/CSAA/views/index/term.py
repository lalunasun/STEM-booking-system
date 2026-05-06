from rest_framework.decorators import api_view, authentication_classes

from CSAA import utils
from CSAA.auth.authentication import AdminTokenAuthtication
from CSAA.handler import APIResponse
from CSAA.models import Term
from CSAA.serializers import TermSerializer


# term列表
@api_view(['GET'])
def list_api(request):
    if request.method == 'GET':
        terms = Term.objects.all()
        serializer = TermSerializer(terms, many=True)
        return APIResponse(code=0, msg='查询成功', data=serializer.data)

