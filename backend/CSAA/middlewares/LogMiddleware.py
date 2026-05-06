import json
import time

from django.utils.deprecation import MiddlewareMixin

from CSAA import utils
from CSAA.serializers import OpLogSerializer

"""
MiddlewareMixin是Django中的一个中间件（Middleware）类，用于方便地将类中定义的中间件方法添加到Django的中间件处理流程中。
Django的中间件机制允许在请求和响应之间进行处理，例如身份验证、请求处理、响应处理等。
中间件可以在请求处理的不同阶段进行操作，以完成各种功能。
MiddlewareMixin通过在类中混合使用该类，并将该类作为第一个父类，使得类中定义的中间件方法可以与已有的中间件方法协同工作。
"""


# 操作日志
class OpLogs(MiddlewareMixin):
    # 初始化
    def __init__(self, *args):
        super(OpLogs, self).__init__(*args)
        self.start_time = None  # 开始时间
        self.end_time = None  # 响应时间
        self.data = {}  # 字典数据

    # 进行请求处理前的逻辑
    def process_request(self, request):
        self.start_time = time.time()  # 开始时间
        re_ip = utils.get_ip(request)
        re_method = request.method
        re_content = request.GET if re_method == 'GET' else request.POST
        if re_content:
            re_content = json.dumps(re_content)
        else:
            re_content = None
        self.data.update(
            {
                're_url': request.path,
                're_method': re_method,
                're_ip': re_ip,
                're_content': re_content,
            }
        )
        # print(self.data)

    # 进行响应处理后的逻辑
    def process_response(self, request, response):
        # 耗时毫秒/ms
        self.end_time = time.time()  # 响应时间
        access_time = self.end_time - self.start_time
        self.data['access_time'] = round(access_time * 1000)

        # 保存入库
        serializer = OpLogSerializer(data=self.data)
        if serializer.is_valid():
            serializer.save()

        return response
