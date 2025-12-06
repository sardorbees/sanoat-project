from django.contrib import admin
from django.shortcuts import redirect
from django.urls import path, include

from django.conf import settings
from django.conf.urls.static import static
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from django.http import HttpResponseForbidden
from django.http import HttpResponse
from rest_framework.authtoken.views import obtain_auth_token
from rest_framework.authtoken.models import Token
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from .views import get_csrf_token
from .templatetags import custom_filters

from django.conf import settings
from django.conf.urls.static import static
from django.conf.urls.i18n import i18n_patterns
from django.views.decorators.csrf import ensure_csrf_cookie
from django.http import JsonResponse

ADMIN_ENABLED = False

@ensure_csrf_cookie
def csrf(request):
    return JsonResponse({'message': 'csrf cookie set'})

def block_admin(request):
    return HttpResponseForbidden("Доступ запрещён")

def block_swagger(request):
    return HttpResponseForbidden("Swagger закрыт")

def home(request):
    return HttpResponse("Главная страница сайта. Админка отключена или включена.")

def home(request):
    return HttpResponse("Xush Sanoat-Korxona Admin")

class AdminAccessControlMiddleware:
    ALLOWED_IPS = ['127.0.0.1']  # разрешённые IP для доступа к админке

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.path.startswith('/admin/') and request.META.get('REMOTE_ADDR') not in self.ALLOWED_IPS:
            return HttpResponseForbidden("Доступ к админке запрещён")
        return self.get_response(request)

schema_view = get_schema_view(
    openapi.Info(
        title="Sanoat-Portali API",
        default_version='v1',
        description="Sanoat - bu har bir davlatning iqtisodiy tayanchi hisoblanadi. Bugungi kunda dunyo bo‘ylab sanoat tarmoqlari texnologik yangiliklar bilan boyimoqda. Energetika, avtomobilsozlik, robototexnika va kimyo sanoati keskin o‘sish sur’atlariga ega. Har bir sanoat tarmog‘i iqtisodiy o‘sishga xizmat qiladi va innovatsion yondashuvlar bilan rivojlanmoqda.",
        terms_of_service="https://www.google.com/policies/terms/",
        contact=openapi.Contact(email="rizotoha1978@gmail.com"),
        license=openapi.License(name="BSD License"),
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
)

item_id_param = openapi.Parameter('id', openapi.IN_PATH, description="ID объекта", type=openapi.TYPE_INTEGER, example=123)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/csrf/', csrf),
    path('', home, name='home'),
    path("api/ckeditor5/", include('django_ckeditor_5.urls')),
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path("api/accounts/", include('accounts.urls')),
    path("api/emails/", include('emails.urls')),
    path("api/phone/", include('phone.urls')),
    path("api/news/", include('news.urls')),
    path("api/chat/", include('chat.urls')),
    path("api/home_section/", include('home_section.urls')),
    path("api/home_desc/", include('home_desc.urls')),
    path("api/home_sectiontwo/", include('home_sectiontwo.urls')),
    path("api/security/", include('security.urls')),
    path("api/application/", include('application.urls')),
    path('i18n/', include('django.conf.urls.i18n')),
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    # path('api/shop/auth/', include('djoser.urls')),
    # path('api/shop/auth/', include('djoser.urls.jwt')),
    path('', lambda request: redirect('schema-swagger-ui')),
]
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

if ADMIN_ENABLED:
    urlpatterns.append(path('admin/', admin.site.urls))