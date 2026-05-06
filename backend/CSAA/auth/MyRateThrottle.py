from rest_framework.throttling import AnonRateThrottle

"""
Rate Throttling用于限制API端点的请求频率，以防止恶意或过多的请求对服务器造成过大的负担。
AnonRateThrottle是其中一种限制方式，它主要用于限制没有进行身份验证的匿名用户的请求频率。
AnonRateThrottle的工作原理是通过对每个匿名用户的请求进行计数，并对其进行限制。
可以设置每个用户在一定时间内允许发送的最大请求数量，以及限制时间段的长度。

每个匿名用户在一天内的请求将受到限制，超过限制的请求将返回429 Too Many Requests响应。

通过使用AnonRateThrottle，可以有效地控制匿名用户的请求频率，以保护服务器免受恶意或过量的请求。
同时，还可以根据实际需求，设置不同的限制规则和时间段长度。
"""


# 匿名用户访问请求次数限制
class MyRateThrottle(AnonRateThrottle):
    THROTTLE_RATES = {"anon": "5/min"}  # 每分钟限制五次
