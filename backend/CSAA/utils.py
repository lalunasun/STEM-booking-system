import datetime
import hashlib
import time


# 订单倒计时
import threading
from CSAA.models import Order


from CSAA.serializers import ErrorLogSerializer


# 获取当前时间的毫秒级时间戳
def get_timestamp():
    return int(round(time.time() * 1000))


# 计算字符串的md5哈希值，小写输出
def md5value(key):
    input_name = hashlib.md5()
    input_name.update(key.encode("utf-8"))
    md5str = (input_name.hexdigest()).lower()
    # print('计算md5:', md5str)
    return md5str


# 封装数据库数据
def dict_fetchall(cursor):  # cursor是执行sql_str后的记录，作为输入参数
    columns = [col[0] for col in cursor.description]  # 得到域的名字col[0]，组成List
    return [
        dict(zip(columns, row)) for row in cursor.fetchall()
    ]


# 获取请求者的IP信息
def get_ip(request):
    """
    request.META.get('HTTP_X_FORWARDED_FOR') 是 Django 中用于获取客户端的真实 IP 地址的一种方法。
    request 是 Django 中的请求对象，META 是该请求对象的一个属性，它包含了请求的元数据，如客户端和服务器之间的通信信息。
    HTTP_X_FORWARDED_FOR 是一个 HTTP 头部字段，它通常由代理服务器添加到请求中。
    这个字段的值是一个逗号分隔的 IP 地址列表，表示这个请求经过了一系列的代理服务器。
    所以，request.META.get('HTTP_X_FORWARDED_FOR') 会返回客户端的真实 IP 地址。
    如果没有经过代理服务器，或者代理服务器没有添加这个字段，那么返回值是 None。
    """
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        """
        request.META.get('REMOTE_ADDR') 是用于获取客户端 IP 地址的一种方法。
        它从请求的元数据中查找 REMOTE_ADDR 字段，并返回客户端的 IP 地址。
        注意，REMOTE_ADDR 只能获取直接连接到服务器的客户端的 IP 地址。
        如果请求通过了代理服务器，那么 REMOTE_ADDR 可能是代理服务器的 IP 地址而不是客户端的真实 IP 地址。
        为了获取客户端的真实 IP 地址，应使用 HTTP_X_FORWARDED_FOR 或其他相关的字段。
        """
        ip = request.META.get('REMOTE_ADDR')
    return ip


# 获取请求者的IP信息
def get_ua(request):
    """
    request.META.get('HTTP_USER_AGENT') 是 Django 中用于获取客户端的用户代理字符串（User-Agent）的一种方法。
    """
    ua = request.META.get('HTTP_USER_AGENT')
    return ua[0:200]


# 获取近一周的日期方法
def getWeekDays():
    week_days = []
    now = datetime.datetime.now()
    for i in range(7):
        day = now - datetime.timedelta(days=i)
        week_days.append(day.strftime('%Y-%m-%d %H:%M:%S.%f')[:10])
    week_days.reverse()  # 逆序
    return week_days


# 获取本周周一日期
def get_monday():
    now = datetime.datetime.now()
    monday = now - datetime.timedelta(now.weekday())
    return monday.strftime('%Y-%m-%d %H:%M:%S.%f')[:10]


# 记录错误日志
def log_error(request, content):
    ip = get_ip(request)
    method = request.method
    url = request.path
    data = {
        'ip': ip,
        'method': method,
        'url': url,
        'content': content
    }

    # 保存数据库
    serializer = ErrorLogSerializer(data=data)
    if serializer.is_valid():
        serializer.save()

#def start_order_countdown(order_number):
    #def cancel_order():
        #try:
            #order = Order.objects.get(pk=order_number)
            #if order.status == '1':
                #order.status = '3'  # 设置订单状态为已取消
                #order.save()
        #except Order.DoesNotExist:
            #pass

    #countdown_thread = threading.Timer(1800, cancel_order)  # 延时 1800 秒（30分钟）
    #countdown_thread.start()