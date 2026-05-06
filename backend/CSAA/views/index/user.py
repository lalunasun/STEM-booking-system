from rest_framework.decorators import api_view, authentication_classes

from CSAA import utils
from CSAA.auth.authentication import TokenAuthtication
from CSAA.handler import APIResponse
from CSAA.models import User
from CSAA.serializers import UserSerializer, LoginLogSerializer
from CSAA.utils import md5value


# 创建登录日志
def make_login_log(request):
    try:
        username = request.data['username']
        data = {
            "username": username,
            "ip": utils.get_ip(request),
            "ua": utils.get_ua(request)
        }
        serializer = LoginLogSerializer(data=data)
        if serializer.is_valid():
            serializer.save()
        else:
            print(serializer.errors)
    except Exception as e:
        print(e)


# 登录
@api_view(['POST'])  # 只接受post请求
def login(request):
    username = request.data['username']
    password = utils.md5value(request.data['password'])
    users = User.objects.filter(username=username, password=password)
    if len(users) > 0:
        user = users[0]
        # 判断是否是管理员账号
        if user.role in ['0']:
            return APIResponse(code=1, msg='该帐号为后台管理员帐号')
        data = {
            'username': username,
            'password': password,
            'token': md5value(username)  # 生成token令牌
        }
        serializer = UserSerializer(user, data=data)
        if serializer.is_valid():
            serializer.save()
            make_login_log(request)
            return APIResponse(code=0, msg='登录成功', data=serializer.data)
        else:
            print(serializer.errors)

    return APIResponse(code=1, msg='用户名或密码错误')


# 注册
@api_view(['POST'])
def register(request):
    username = request.data.get('username', None)
    password = request.data.get('password', None)
    repassword = request.data.get('repassword', None)
    if not username or not password or not repassword:
        return APIResponse(code=1, msg='用户名或密码不能为空')
    if password != repassword:
        return APIResponse(code=1, msg='密码不一致')
    users = User.objects.filter(username=username)
    if len(users) > 0:
        return APIResponse(code=1, msg='该用户名已存在')

    data = {
        'username': username,
        'password': password,
        'role': 2,  # 角色2，普通用户
        'status': 0,
    }
    data.update({'password': utils.md5value(request.data['password'])})
    serializer = UserSerializer(data=data)
    if serializer.is_valid():
        serializer.save()
        return APIResponse(code=0, msg='创建成功', data=serializer.data)
    else:
        print(serializer.errors)

    return APIResponse(code=1, msg='创建失败')


# 用户信息
@api_view(['GET'])  # 只接受get请求
def info(request):
    if request.method == 'GET':
        pk = request.GET.get('id', -1)
        user = User.objects.get(pk=pk)
        serializer = UserSerializer(user)
        return APIResponse(code=0, msg='查询成功', data=serializer.data)


# 修改个人信息
@api_view(['POST'])
@authentication_classes([TokenAuthtication])  # 普通用户token认证
def update(request):
    try:
        pk = request.GET.get('id', -1)
        user = User.objects.get(pk=pk)
    except User.DoesNotExist:
        return APIResponse(code=1, msg='用户不存在')


    serializer = UserSerializer(user, data=request.data)
    # print(serializer.is_valid())
    if serializer.is_valid():
        serializer.save()
        return APIResponse(code=0, msg='更新成功', data=serializer.data)
    else:
        print(serializer.errors)

    return APIResponse(code=1, msg='更新失败')


# 修改密码
@api_view(['POST'])
@authentication_classes([TokenAuthtication])
def updatePwd(request):
    try:
        pk = request.GET.get('id', -1)
        user = User.objects.get(pk=pk)
    except User.DoesNotExist:
        return APIResponse(code=1, msg='用户不存在')

    # print(user.role)
    if user.role != '2':
        return APIResponse(code=1, msg='修改密码输入参数非法')

    # 获取输入数据
    password = request.data.get('password', None)
    newPassword1 = request.data.get('newPassword1', None)
    newPassword2 = request.data.get('newPassword2', None)

    # 验证校验密码
    if not password or not newPassword1 or not newPassword2:
        return APIResponse(code=1, msg='不能为空')
    if user.password != utils.md5value(password):
        return APIResponse(code=1, msg='原密码不正确')
    if newPassword1 != newPassword2:
        return APIResponse(code=1, msg='两次密码不一致')
    # 存入数据库
    data = request.data.copy()
    data.update({'password': utils.md5value(newPassword1)})
    serializer = UserSerializer(user, data=data)
    if serializer.is_valid():
        serializer.save()
        return APIResponse(code=0, msg='更新成功', data=serializer.data)
    else:
        print(serializer.errors)

    return APIResponse(code=1, msg='更新失败')
