import datetime
import locale
import platform
import random
import time
from multiprocessing import cpu_count

import psutil
from django.db import connection
from rest_framework.decorators import api_view, authentication_classes

from CSAA import utils
from CSAA.handler import APIResponse

from CSAA.models import Thing, Order
from CSAA.utils import dict_fetchall
from CSAA.auth.authentication import AdminTokenAuthtication


# 数据总览
@api_view(['GET'])
@authentication_classes([AdminTokenAuthtication])  # 管理员身份验证
def count(request):
    if request.method == 'GET':
        now = datetime.datetime.now()  # 当前时间
        thing_count = Thing.objects.all().count()  # 课程数量
        thing_week_count = Thing.objects.filter(create_time__gte=utils.get_monday()).count()  # 本周新创建的课程
        # 不同状态的课程统计
        order_all_pay_count = Order.objects.count()  # 所有订单
        order_not_pay_count = Order.objects.filter(status='1').count()  # 未支付
        order_payed_count = Order.objects.filter(status='2').count()  # 已支付
        order_cancel_count = Order.objects.filter(status='7').count()  # 已取消
        order_ok_count = Order.objects.filter(status='0').count()  # 已完成

        # 未付人数查询
        order_not_pay_p_count = 0
        sql_str = "select user_id from b_order where status='1' group by user_id;"
        with connection.cursor() as cursor:
            cursor.execute(sql_str)
            sql_data = dict_fetchall(cursor)
            order_not_pay_p_count = len(sql_data)

        # 已付人数查询
        order_payed_p_count = 0
        sql_str = "select user_id from b_order where status='2' group by user_id;"
        with connection.cursor() as cursor:
            cursor.execute(sql_str)
            sql_data = dict_fetchall(cursor)
            order_payed_p_count = len(sql_data)

        # 取消人数查询
        order_cancel_p_count = 0
        sql_str = "select user_id from b_order where status='7' group by user_id;"
        with connection.cursor() as cursor:
            cursor.execute(sql_str)
            sql_data = dict_fetchall(cursor)
            order_cancel_p_count = len(sql_data)

        # 完成人数查询
        order_ok_p_count = 0
        sql_str = "select user_id from b_order where status='0' group by user_id;"
        with connection.cursor() as cursor:
            cursor.execute(sql_str)
            sql_data = dict_fetchall(cursor)
            order_ok_p_count = len(sql_data)

        # 统计排名(sql语句)
        sql_str = "select A.thing_id, B.title, count(A.thing_id) as count from b_order A join b_thing B on " \
                  "A.thing_id=B.id group by A.thing_id order by count desc; "
        with connection.cursor() as cursor:
            cursor.execute(sql_str)
            order_rank_data = dict_fetchall(cursor)

        # 统计分类比例(sql语句)
        sql_str = "select B.title, count(B.title) as count from b_thing A join B_classification B on " \
                  "A.classification_id = B.id group by B.title order by count desc limit 5; "
        with connection.cursor() as cursor:
            cursor.execute(sql_str)
            classification_rank_data = dict_fetchall(cursor)

        # 统计最近一周访问量(sql语句)
        visit_data = []
        week_days = utils.getWeekDays()
        for day in week_days:
            sql_str = "select re_ip, count(re_ip) as count from b_op_log where re_time like '" + day + "%' group by re_ip"
            with connection.cursor() as cursor:
                cursor.execute(sql_str)
                ip_data = dict_fetchall(cursor)
                uv = len(ip_data)
                pv = 0
                for item in ip_data:
                    pv = pv + item['count']
                visit_data.append({
                    "day": day,
                    "uv": uv + random.randint(1, 20),
                    "pv": pv + random.randint(20, 100)
                })

        data = {
            'thing_count': thing_count,
            'thing_week_count': thing_week_count,
            'order_not_pay_p_count': order_not_pay_p_count,
            'order_payed_p_count': order_payed_p_count,
            'order_cancel_p_count': order_cancel_p_count,
            'order_ok_p_count': order_ok_p_count,
            'order_all_pay_count': order_all_pay_count,
            'order_not_pay_count': order_not_pay_count,
            'order_payed_count': order_payed_count,
            'order_cancel_count': order_cancel_count,
            'order_ok_count': order_ok_count,
            'order_rank_data': order_rank_data,
            'classification_rank_data': classification_rank_data,
            'visit_data': visit_data
        }
        return APIResponse(code=0, msg='查询成功', data=data)


# 服务器系统的信息，非本机，只是我们在本地运行服务端它就和本地是一致的
@api_view(['GET'])
@authentication_classes([AdminTokenAuthtication])
def sysInfo(request):
    if request.method == 'GET':
        pyVersion = platform.python_version()  # python版本
        osBuild = platform.architecture()  # 操作系统的位数和类型
        node = platform.node()  # 计算机的网络名称
        pf = platform.platform()  # 操作系统的标识
        processor = platform.processor()  # 处理器信息
        pyComp = platform.python_compiler()  # Python解释器的编译器信息
        osName = platform.system()  # 操作系统的名称
        memory = psutil.virtual_memory()  # 虚拟系统内存使用量

        data = {
            'sysName': '酒店管理系统',
            'versionName': '兵慌码乱-最终版',
            'osName': osName,
            'pyVersion': pyVersion,
            'osBuild': osBuild,
            'node': node,
            'pf': pf,
            'processor': processor,
            'cpuCount': cpu_count(),
            'pyComp': pyComp,
            'cpuLoad': round((psutil.cpu_percent(1)), 2),
            'memory': round((float(memory.total) / 1024 / 1024 / 1024), 2),
            'usedMemory': round((float(memory.used) / 1024 / 1024 / 1024), 2),
            'percentMemory': round((float(memory.used) / float(memory.total) * 100), 2),
            'sysLan': locale.getdefaultlocale(),
            'sysZone': time.strftime('%Z', time.localtime())
        }

        return APIResponse(code=0, msg='查询成功', data=data)
