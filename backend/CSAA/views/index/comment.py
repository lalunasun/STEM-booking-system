from rest_framework.decorators import api_view, throttle_classes

from CSAA.auth.MyRateThrottle import MyRateThrottle
from CSAA.handler import APIResponse
from CSAA.models import Comment
from CSAA.serializers import CommentSerializer


# 评论列表
@api_view(['GET'])
def list_api(request):
    if request.method == 'GET':
        thingId = request.GET.get("thingId", None)
        order = request.GET.get("order", 'recent')

        # 排序方式
        if thingId:
            if order == 'recent':
                orderBy = '-comment_time'
            else:
                orderBy = '-like_count'

            # 查询所有评论信息
            comments = Comment.objects.select_related("thing").filter(thing=thingId).order_by(orderBy)
            serializer = CommentSerializer(comments, many=True)
            return APIResponse(code=0, msg='查询成功', data=serializer.data)
        else:
            return APIResponse(code=1, msg='thingId不能为空')


# 我的评论列表
@api_view(['GET'])
def list_my_comment(request):
    if request.method == 'GET':
        userId = request.GET.get("userId", None)
        order = request.GET.get("order", 'recent')  # 排序方式

        if userId:
            if order == 'recent':
                orderBy = '-comment_time'
            else:
                orderBy = '-like_count'

            comments = Comment.objects.select_related("thing").filter(user=userId).order_by(orderBy)
            serializer = CommentSerializer(comments, many=True)
            return APIResponse(code=0, msg='查询成功', data=serializer.data)
        else:
            return APIResponse(code=1, msg='userId不能为空')


# 创建评论
@api_view(['POST'])
@throttle_classes([MyRateThrottle])
def create(request):
    serializer = CommentSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return APIResponse(code=0, msg='创建成功', data=serializer.data)
    else:
        print(serializer.errors)

    return APIResponse(code=1, msg='创建失败')


# 删除评论
@api_view(['POST'])
def delete(request):
    try:
        ids = request.GET.get('ids')
        ids_arr = ids.split(',')
        Comment.objects.filter(id__in=ids_arr).delete()
    except Comment.DoesNotExist:
        return APIResponse(code=1, msg='评论不存在')

    return APIResponse(code=0, msg='删除成功')


# 添加点赞
@api_view(['POST'])
def like(request):
    try:
        commentId = request.GET.get('commentId')
        comment = Comment.objects.get(pk=commentId)
        comment.like_count += 1
        comment.save()
    except Comment.DoesNotExist:
        return APIResponse(code=1, msg='评论不存在')

    return APIResponse(code=0, msg='点赞推荐成功')
