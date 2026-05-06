from rest_framework.decorators import api_view, authentication_classes

from CSAA.auth.authentication import AdminTokenAuthtication
from CSAA.handler import APIResponse
from CSAA.models import Comment
from CSAA.serializers import CommentSerializer


# 评论列表
@api_view(['GET'])
def list_api(request):
    if request.method == 'GET':
        comments = Comment.objects.select_related("thing").all().order_by('-comment_time')
        serializer = CommentSerializer(comments, many=True)
        return APIResponse(code=0, msg='查询成功', data=serializer.data)


# 创建评论
@api_view(['POST']) # 直接受post请求
@authentication_classes([AdminTokenAuthtication]) # 管理员身份验证
def create(request):
    serializer = CommentSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return APIResponse(code=0, msg='创建成功', data=serializer.data)
    else:
        print(serializer.errors)

    return APIResponse(code=1, msg='创建失败')


# 修改评论
@api_view(['POST'])
@authentication_classes([AdminTokenAuthtication])
def update(request):
    try:
        pk = request.GET.get('id', -1)
        comments = Comment.objects.get(pk=pk)
    except Comment.DoesNotExist:
        return APIResponse(code=1, msg='评论不存在')

    serializer = CommentSerializer(comments, data=request.data)
    if serializer.is_valid():
        serializer.save()
        return APIResponse(code=0, msg='更新成功', data=serializer.data)

    return APIResponse(code=1, msg='更新失败')


# 删除评论
@api_view(['POST'])
@authentication_classes([AdminTokenAuthtication])
def delete(request):
    try:
        ids = request.GET.get('ids')
        ids_arr = ids.split(',')
        Comment.objects.filter(id__in=ids_arr).delete()
    except Comment.DoesNotExist:
        return APIResponse(code=1, msg='评论不存在')

    return APIResponse(code=0, msg='删除成功')
