from rest_framework import exceptions
from rest_framework.authentication import BaseAuthentication

from CSAA.models import User

"""
BaseAuthentication是Django REST Framework（DRF）中的一个基类，用于实现自定义身份验证（Authentication）类。
所有的身份验证类都应继承自BaseAuthentication，并实现其两个方法：authenticate和authenticate_header。

authenticate(request): 在这个方法中，我们可以根据请求中的信息（如请求头、查询参数等）来验证用户的身份。
这个方法需要返回一个元组 (user, auth) ，其中 user 表示认证成功的用户对象，auth 表示认证使用的身份验证类的实例。
如果认证失败，则返回 None。

authenticate_header(request): 这个方法返回一个字符串，表示在认证失败时需要在响应头中返回的信息，用于指示客户端如何进行身份验证。

BaseAuthentication是一个抽象基类，无法直接使用，需要根据具体的情况，实现自定义的身份验证类，并继承自BaseAuthentication。
DRF还提供了一些常用的身份验证类（如TokenAuthentication、SessionAuthentication等），
它们已经继承了BaseAuthentication，并实现了相应的验证逻辑。
"""


# 身份认证
class AdminTokenAuthtication(BaseAuthentication):
    def authenticate(self, request):
        adminToken = request.META.get("HTTP_ADMINTOKEN", "")
        users = User.objects.filter(admin_token=adminToken, role='0')
        """
        判定条件：
            1. 传了adminToken 
            2. 查到了该帐号 
            3. 该帐号是管理员
        """
        if not adminToken or len(users) == 0:
            raise exceptions.AuthenticationFailed("管理员身份认证失败！")
        return users[0], adminToken


# 身份认证
class TokenAuthtication(BaseAuthentication):
    def authenticate(self, request):
        token = request.META.get("HTTP_TOKEN", "")
        if token is not None:
            print("检查token==>" + token)
            users = User.objects.filter(token=token)
            """
            判定条件：
                1. 传了token 
                2. 查到了该帐号 
                3. 该帐号是普通用户
            """

            if not token or len(users) == 0:
                raise exceptions.AuthenticationFailed("用户身份验证失败！")
            else:
                print('token验证通过')
        else:
            print("检查token==>token 为空")
            raise exceptions.AuthenticationFailed("用户身份验证失败！")
