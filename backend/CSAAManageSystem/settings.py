import os

# 项目路径
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# 项目秘钥
SECRET_KEY = 'django-insecure-sz@madp0ifx!b)^lg_g!f+5s*w7w_=sjgq-k+erzb%x42$^r!d'

# 调试模式
DEBUG = True

# 允许的主机
ALLOWED_HOSTS = ['*']

# 注册app
INSTALLED_APPS = [
    'django.contrib.admin',  # 后台管理模块
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',  # drf
    'corsheaders',  # 跨域
    'CSAA'  # CSAA管理模块
]

# 中间件
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware',  # 跨域配置
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'CSAA.middlewares.LogMiddleware.OpLogs'  # 自定的中间件
]


# 根路由
ROOT_URLCONF = 'CSAAManageSystem.urls'

# 模板文件配置
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'CSAAManageSystem.wsgi.application'

# 数据库配置
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
    }
}

# 密码验证
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# 国际化配置
LANGUAGE_CODE = 'zh-hans'
TIME_ZONE = 'Asia/Shanghai'
USE_I18N = True
USE_L10N = True
USE_TZ = False

# 日期时间格式
DATE_FORMAT = 'Y-m-d'
DATETIME_FORMAT = 'Y-m-d H:i:s'

# 上传文件路径
# 并在urls.py配置+static
MEDIA_ROOT = os.path.join(BASE_DIR, 'upload/')
MEDIA_URL = '/upload/'

# 静态文件 (CSS, JavaScript, Images)
STATIC_URL = 'static/'

# 主键自增
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'


'''
Django的跨域问题指的是在使用Django框架进行开发时，由于浏览器的同源策略限制，导致前端页面无法直接访问不同域名、不同端口或不同协议的接口。
在这种情况下，如果前端页面需要访问其他域名的接口，就会出现跨域问题。
为了解决跨域问题，Django提供了一些解决方案：
使用Django自带的CSRF中间件和CSRF cookie：Django会自动生成一个CSRF token，并将其保存在cookie中。在发送跨域请求时，需要在请求头中携带该token，以通过服务器的CSRF验证。
使用Django的CORS扩展（Cross-Origin Resource Sharing）：CORS扩展可以在Django项目中配置允许跨域的策略，包括允许哪些域名、方法和头部。
在Django中使用中间件处理跨域问题：可以自定义一个中间件，在每个请求中添加必要的响应头，如"Access-Control-Allow-Origin"、"Access-Control-Allow-Methods"等。
需要注意的是，配置跨域策略时需要考虑安全性和合规性，并谨慎配置允许跨域的域名、方法和头部，以防止恶意攻击或数据泄漏。
'''
# 允许跨域
CORS_ORIGIN_ALLOW_ALL = True
# 跨域配置
# 允许跨域请求携带认证信息（例如Cookie和HTTP认证头）
CORS_ALLOW_CREDENTIALS = True
# 表示允许所有的域名进行跨域访问
CORS_ALLOW_ALL_ORIGINS = True
# 表示允许所有的请求头进行跨域访问
CORS_ALLOW_HEADERS = '*'
