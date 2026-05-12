from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path, re_path

from CSAAManageSystem import settings
from CSAAManageSystem.frontend import serve_frontend_app, serve_frontend_asset


urlpatterns = [
    path('django-admin/', admin.site.urls),
    path('CSAA/', include('CSAA.urls')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT) + [
    re_path(r'^(?P<path>(assets|images)/.*)$', serve_frontend_asset),
    re_path(r'^(?P<path>.*)$', serve_frontend_app),
]
