from pathlib import Path
BASE_DIR = Path(__file__).resolve().parent.parent
SECRET_KEY = '*'
DEBUG = True
ALLOWED_HOSTS = [
    '*',
]
from django.views.generic import View
from django.http import HttpResponse
from django.conf import settings
import json
import os

from django.contrib import messages
from django.contrib.admin import ModelAdmin
from django.core.exceptions import ValidationError
from django.db.models import Q
from django.utils.translation import gettext_lazy as _

from cryptography.fernet import Fernet

FERNET_KEY = Fernet.generate_key()
fernet = Fernet(FERNET_KEY)

class AdvancedSearchAdmin(ModelAdmin):
    """
        class to add custom filters in django admin
    """
    change_list_template = 'admin/custom_change_list.html'
    advanced_search_fields = {}
    search_form_data = None

    def get_queryset(self, request):
        """
            override django admin 'get_queryset'
        """
        queryset = super().get_queryset(request)
        try:
            return queryset.filter(self.advanced_search_query(request))
        except Exception:  # pylint: disable=broad-except
            messages.add_message(request, messages.ERROR, 'Filter not applied, error has occurred')
            return queryset.none()

    def changelist_view(self, request, extra_context=None):
        """
            Append custom form to page render
        """
        extra_context = extra_context or {}
        if hasattr(self, 'search_form'):
            self.advanced_search_fields = {}
            self.search_form_data = self.search_form(request.GET.dict())
            self.extract_advanced_search_terms(request.GET)
            extra_context.update({'asf': self.search_form_data})

        return super().changelist_view(request, extra_context=extra_context)

    def extract_advanced_search_terms(self, request):
        """
            allow to extract field values from request
        """
        request._mutable = True  # pylint: disable=protected-access

        if self.search_form_data is not None:
            for key in self.search_form_data.fields.keys():
                temp = request.pop(key, None)
                if temp:  # there is a field but it's empty so it's useless
                    self.advanced_search_fields[key] = temp

        request._mutable = False  # pylint: disable=protected-access

    def get_request_field_value(self, field):
        """
            check if field has value passed on request
        """
        if field in self.advanced_search_fields:
            value = self.advanced_search_fields[field][0]
            return bool(value), value

        return False, None

    @staticmethod
    def get_field_value_default(field, form_field, field_value, has_field_value, request):
        """
            mount default field value
        """
        if has_field_value:
            field_name = form_field.widget.attrs.get('filter_field', field)
            field_filter = field_name + form_field.widget.attrs.get('filter_method', '')

            try:
                field_value = utils.format_data(form_field, field_value)  # format by field type
                return Q(**{field_filter: field_value})
            except ValidationError:
                messages.add_message(request, messages.ERROR, _(
                    f"Filter in field `{field_name}` ignored, because value `{field_value}` isn't valid."))
            except Exception:  # pylint: disable=broad-except
                messages.add_message(request, messages.ERROR, _(
                    f"Filter in field `{field_name}` ignored, an error has occurred in filtering."))

        return Q()

    def get_field_value(self, field, form_field, field_value, has_field_value, request):
        """
            allow to override default field query
        """
        if hasattr(self, ('search_' + field)):
            return getattr(self, 'search_' + field)(field, field_value, form_field, request,
                                                    self.advanced_search_fields)

        return self.get_field_value_default(field, form_field, field_value, has_field_value, request)

    def advanced_search_query(self, request):
        """
            Get form and mount filter query if form is not none
        """
        query = Q()

        if self.search_form_data is None:
            return query

        for field, form_field in self.search_form_data.fields.items():
            has_field_value, field_value = self.get_request_field_value(field)
            query &= self.get_field_value(field, form_field, field_value, has_field_value, request)

        return query


class FrontendAppView(View):
    def get(self, request):
        try:
            with open(os.path.join(settings.REACT_APP_DIR, 'build', 'index.html')) as f:
                return HttpResponse(f.read())
        except FileNotFoundError:
            return HttpResponse(
                "index.html not found, build your React app first", status=501,
            )

# settings.py
from decouple import config
from cryptography.fernet import Fernet

FERNET_KEY = config("FERNET_KEY").encode()
FERNET = Fernet(FERNET_KEY)

# Fernet keys support (rotation). Храни ключи в env или KMS/VAULT.
# Format: FERNET_KEYS="current_key,old_key1,old_key2"
FERNET_KEYS_RAW = os.environ.get("FERNET_KEYS")  # comma separated base64 keys
if FERNET_KEYS_RAW:
    FERNET_KEYS = [k.strip() for k in FERNET_KEYS_RAW.split(",") if k.strip()]
else:
    # fallback: single key
    SINGLE_FERNET_KEY = os.environ.get("FERNET_KEY")
    FERNET_KEYS = [SINGLE_FERNET_KEY] if SINGLE_FERNET_KEY else []


SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

SECURE_SSL_REDIRECT = False
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False

# HMAC key for indexing/searching (never store in repo)
HMAC_KEY = os.environ.get("HMAC_KEY")  # hex or raw bytes string

import os

AES_KEY = os.environ.get("AES_KEY")
HMAC_SECRET_KEY = os.environ.get("HMAC_SECRET_KEY")

if not AES_KEY:
    AES_KEY = os.urandom(32).hex()

if not HMAC_SECRET_KEY:
    HMAC_SECRET_KEY = os.urandom(32).hex()

# Пароли — использовать Argon2
PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.Argon2PasswordHasher",       # preferred
    "django.contrib.auth.hashers.PBKDF2PasswordHasher",
    "django.contrib.auth.hashers.PBKDF2SHA1PasswordHasher",
]

INSTALLED_APPS = [
    'jazzmin',
    'django.contrib.humanize',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django_ckeditor_5',
    'rest_framework.authtoken',
    'rest_framework',
    'channels',
    'chat',
    'rest_framework_simplejwt',
    'drf_yasg', 
    'corsheaders',
    'accounts',
    'django_filters',
    'application',
    'home_desc',
    'emails',
    'phone',
    'news',
    'home_section',
    'home_sectiontwo',
    'security'
]

CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": "redis://127.0.0.1:6379/1",
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
        }
    }
}

CELERY_BROKER_URL = 'redis://127.0.0.1:6379/0'
CELERY_RESULT_BACKEND = 'redis://127.0.0.1:6379/0'
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = 'Asia/Tashkent'

import os
from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'my_cleaning.settings')

app = Celery('my_cleaning')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()


ESKIZ_API_KEY = "твoй_API_ключ_из_eskiz"
SMS_SENDER = "MyCompany"

from decouple import config

REDIS_URL = "redis://127.0.0.1:6379/0"

API_RATE_LIMIT = {
    "IP": {"per_minute": 60, "burst": 5},
    "PHONE_OTP": {"per_minute": 5, "burst": 2}
}

# Telegram (для уведомлений)
TELEGRAM_BOT_TOKEN = ""   # вставь токен
TELEGRAM_CHAT_ID = ""     # вставь chat_id

# Token rotation
API_TOKEN_ROTATION_DAYS = 1

LANGUAGES = (
    ('ru', 'Russian'),
    ('uz', 'Uzbek'),
)

MODELTRANSLATION_DEFAULT_LANGUAGE = 'ru'
MODELTRANSLATION_LANGUAGES = ('ru', 'uz')
MODELTRANSLATION_PREPOPULATE_LANGUAGE = 'ru'

DJOSER = {
    "USER_ID_FIELD": "id",
    "LOGIN_FIELD": "username",
    'LOGIN_EMAIL': 'email',
    "SERIALIZERS": {
        "user_create": "djoser.serializers.UserCreateSerializer",
        "user": "djoser.serializers.UserSerializer",
    },
}

CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels_redis.core.RedisChannelLayer",
        "CONFIG": {
            "hosts": [("127.0.0.1", 6379)],
        },
    },
}

CLICK_SETTINGS = {
    'service_id': "<Ваш сервис ID>",
    'merchant_id': "<Ваш merchant ID>",
    'secret_key': "<Ваш секретный ключ>",
    'merchant_user_id': "<Ваш merchant user ID>",
}

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'simple': {
            'format': '[{levelname}] {message}',
            'style': '{',
        },
    },
    'handlers': {
        'null': {
            'class': 'logging.NullHandler',
        },
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
        },
    },
    'loggers': {
        'django.server': {
            'handlers': ['null'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}

AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
    'emails.auth_backends.EmailBackend',
]


RECAPTCHA_SECRET_KEY = os.getenv('6Lc7ioArAAAAABqG07AEM2vHo3gD2fe7dJOh8DtB')

TELEGRAM_BOT_TOKEN = '7613975897:AAHSzOal47p9jeu62JR1sdI23-mQyb3Sk50'
TELEGRAM_CHAT_ID = '7139975148'

X_FRAME_OPTIONS='SAMEORIGIN'

EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = "smtp.gmail.com"
EMAIL_USE_TLS = True
EMAIL_PORT = 587
EMAIL_HOST_USER = "rizotoha1978@gmail.com"
EMAIL_HOST_PASSWORD = "xfrv axgq xiyl hhjz"
DEFAULT_FROM_EMAIL = EMAIL_HOST_USER

AUTH_USER_MODEL = 'accounts.CustomUser'

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'security.middleware.RateLimitMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    "accounts.middleware.ForcePasswordChangeMiddleware",
    'security.middleware.UserSessionMiddleware',
]
LOGIN_REDIRECT_URL = '/admin/'
LOGIN_URL = '/admin/'

# Email
DEFAULT_FROM_EMAIL = 'admin@gmail.com'

# Telegram
TELEGRAM_BOT_TOKEN = '8569067597:AAG5tGRlyAJWCm4iGbUDu39_bH_3kohpgVo'
TELEGRAM_CHAT_ID = '@auth_sanoat'  # для теста можно свой

# SMS (пример Eskiz)
SMS_API_URL = 'https://api.eskiz.uz'
SMS_API_KEY = 'tvF4OWO2dXEu7ejGc7WGIjkmNA2prIQOXbzIR7q6'
SMS_SENDER = 'Example'


ROOT_URLCONF = 'my_cleaning.urls'


TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [
            BASE_DIR / 'templates'
        ],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',  # Required for admin sidebar
                'django.contrib.auth.context_processors.auth',  # Required for admin
                'django.contrib.messages.context_processors.messages',  # Required for admin
            ],
        },
    },
]

WSGI_APPLICATION = 'my_cleaning.wsgi.application'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

import os

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Password validation
# https://docs.djangoproject.com/en/5.1/ref/settings/#auth-password-validators

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


# Internationalization
# https://docs.djangoproject.com/en/5.1/topics/i18n/


from django.utils.translation import gettext_lazy as _

LANGUAGE_CODE = "ru"

LANGUAGES = [
    ('ru', 'Русский'),
    ('uz', 'Oʻzbekcha'),
]

TIME_ZONE = "Asia/Tehran"
USE_I18N = True
USE_L10N = True
USE_TZ = True

import os
TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")

LOCALE_PATHS = [
    os.path.join(BASE_DIR, 'locale'),
]

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.1/howto/static-files/

STATIC_URL = '/staticfiles/'
STATICFILES_DIRS = [ BASE_DIR / 'staticfiles' ]
STATIC_ROOT = BASE_DIR / 'staticfiles'

# Default primary key field type
# https://docs.djangoproject.com/en/5.1/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

customColorPalette = [
    {
        'color': 'hsl(4, 90%, 58%)',
        'label': 'Red'
    },
    {
        'color': 'hsl(340, 82%, 52%)',
        'label': 'Pink'
    },
    {
        'color': 'hsl(291, 64%, 42%)',
        'label': 'Purple'
    },
    {
        'color': 'hsl(262, 52%, 47%)',
        'label': 'Deep Purple'
    },
    {
        'color': 'hsl(231, 48%, 48%)',
        'label': 'Indigo'
    },
    {
        'color': 'hsl(207, 90%, 54%)',
        'label': 'Blue'
    },
]

CKEDITOR_5_CONFIGS = {
    'default': {
        'toolbar': ['heading', '|', 'bold', 'italic', 'link',
                    'bulletedList', 'numberedList', 'blockQuote', 'imageUpload', ],

    },
    'extends': {
        'blockToolbar': [
            'paragraph', 'heading1', 'heading2', 'heading3',
            '|',
            'bulletedList', 'numberedList',
            '|',
            'blockQuote',
        ],
        'toolbar': ['heading', '|', 'outdent', 'indent', '|', 'bold', 'italic', 'link', 'underline', 'strikethrough',
                    'code', 'subscript', 'superscript', 'highlight', '|', 'codeBlock', 'sourceEditing', 'insertImage',
                    'bulletedList', 'numberedList', 'todoList', '|', 'blockQuote', 'imageUpload', '|',
                    'fontSize', 'fontFamily', 'fontColor', 'fontBackgroundColor', 'mediaEmbed', 'removeFormat',
                    'insertTable', ],
        'image': {
            'toolbar': ['imageTextAlternative', '|', 'imageStyle:alignLeft',
                        'imageStyle:alignRight', 'imageStyle:alignCenter', 'imageStyle:side', '|'],
            'styles': [
                'full',
                'side',
                'alignLeft',
                'alignRight',
                'alignCenter',
            ]

        },
        'table': {
            'contentToolbar': ['tableColumn', 'tableRow', 'mergeTableCells',
                               'tableProperties', 'tableCellProperties'],
            'tableProperties': {
                'borderColors': customColorPalette,
                'backgroundColors': customColorPalette
            },
            'tableCellProperties': {
                'borderColors': customColorPalette,
                'backgroundColors': customColorPalette
            }
        },
        'heading': {
            'options': [
                {'model': 'paragraph', 'title': 'Paragraph', 'class': 'ck-heading_paragraph'},
                {'model': 'heading1', 'view': 'h1', 'title': 'Heading 1', 'class': 'ck-heading_heading1'},
                {'model': 'heading2', 'view': 'h2', 'title': 'Heading 2', 'class': 'ck-heading_heading2'},
                {'model': 'heading3', 'view': 'h3', 'title': 'Heading 3', 'class': 'ck-heading_heading3'}
            ]
        }
    },
    'list': {
        'properties': {
            'styles': 'true',
            'startIndex': 'true',
            'reversed': 'true',
        }
    }
}

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
        'rest_framework.authentication.SessionAuthentication',
    ),
    "DEFAULT_PERMISSION_CLASSES": ("rest_framework.permissions.IsAuthenticated",),
}


SWAGGER_SETTINGS = {
    'SECURITY_DEFINITIONS': {
        'Bearer': {
            'type': 'apiKey',
            'name': 'Authorization',
            'in': 'header'
        }
    },
    'USE_SESSION_AUTH': True,
}


CORS_ALLOW_ALL_ORIGINS = True

CORS_ALLOWED_ORIGINS = [
    "https://sanoat-portal-backend.onrender.com",
    "https://maftun-mebel.vercel.app",
]

CORS_ALLOW_CREDENTIALS = True

CSRF_COOKIE_NAME = "csrftoken"
CSRF_COOKIE_SAMESITE = "Lax"
CSRF_COOKIE_SECURE = True

CSRF_TRUSTED_ORIGINS = [
    "https://maftun-mebel.vercel.app",
    "https://sanoat-portal-backend.onrender.com",
]

CSRF_COOKIE_HTTPONLY = False

CORS_ALLOW_HEADERS = [
    'authorization',
    'content-type',
    'x-csrftoken',
    'x-requested-with',
]


CORS_ALLOW_METHODS = [
    'GET',
    'POST',
    'PUT',
    'PATCH',
    'DELETE',
    'OPTIONS',
]

STATIC_URL = '/static/'

STATICFILES_DIRS = [
    BASE_DIR / "static",  # или путь, который реально существует
]

STATIC_ROOT = BASE_DIR / 'staticfiles'

JAZZMIN_SETTINGS = {
    "site_title": "Sanoat-Korxona",
    "site_header": "Sanoat-Korxona",
    "site_brand": "Sanoat-Korxona",
    "site_icon": "../media/assets/maftun-mebel.jpg",
    "site_logo": "../media/assets/maftun-mebel.png",
    "language_chooser": True,
    "changeform_format": "horizontal_tabs",
    "changeform_format_overrides": {"auth.user": "collapsible", "auth.group": "vertical_tabs"},
    "welcome_sign": "Xush Kelibsiz Sanoat-Korxona",
    "copyright": "Sanoat-Korxona-Admin",
    "user_avatar": "../media/assets/maftun-mebel.jpg",
    "dashboard": [
        {"type": "link", "title": "Documentation", "url": "http://127.0.0.1:8000/swagger/"},
    ],
    "topmenu_links": [
        {"name": "Sanoat-Korxona.uz", "url": "https://maftun-mebel.uz", "permissions": ["auth.view_user"]},
        # {"name": "Telegram", "url": "https://t.me/Mebelshitsa", "permissions": ["auth.view_user"]},
        # {"name": "Instagram", "url": "https://www.instagram.com/ashirmatabdukodirov?utm_source=qr&igsh=N2JodndrMmpoMWd3", "permissions": ["auth.view_user"]},
        {"model": "auth.User"},
        {"app": "books"},
    ],
    "custom_links": {
        "books": [{
            "name": "Make Messages",
            "url": "make_messages",
            "icon": "fas fa-comments",
            "permissions": ["books.view_book"]
        }]
    },
    "usermenu_links": [
        {"model": "auth.user"}
    ],

    "show_sidebar": True,
    "navigation_expanded": None,
    "icons": {
        "auth": "fa-solid fa-headset",
        "auth.user": "fa-solid fa-headset",
        "auth.Group": "fas fa-users",
        "your_app.ModelName": "fa-solid fa-headset",
    },
    "default_icon_parents": "fa-solid fa-headset",
    "default_icon_children": "fa-solid fa-solar-panel",
    "related_modal_active": True,
    "custom_js": True,
    "hide_apps": [],
    "hide_models": [],
    "order_with_respect_to": ["auth", "your_app_name"],
    "show_ui_builder": True,
}

TINYMCE_DEFAULT_CONFIG = {
    'theme': 'advanced',
    'relative_urls': False,
    'plugins': 'media,spellchecker',
    'content_style': '.mcecontentbody{font-size:13px;}',
    'theme_advanced_buttons1': 'bold,italic,underline,bullist,numlist,|,link,unlink,image',
    'theme_advanced_resizing': True,
    'theme_advanced_path': False,
}

TINYMCE_DEFAULT_CONFIG = {
    'theme': 'advanced',
    'relative_urls': False,
    'plugins': 'media,spellchecker',
    'content_style': '.mcecontentbody{font-size:13px;}',
    'theme_advanced_buttons1': 'bold,italic,underline,bullist,numlist,|,link,unlink,image',
    'theme_advanced_resizing': True,
    'theme_advanced_path': False,
}

JAZZMIN_UI_TWEAKS = {
    "navbar_small_text": True,
    "footer_small_text": True,
    "body_small_text": True,
    "brand_small_text": True,
    "brand_colour": "navbar-success",
    "accent": "accent-teal",
    "navbar": "navbar-dark",
    "no_navbar_border": True,
    "navbar_fixed": True,
    "layout_boxed": False,
    "footer_fixed": True,
    "sidebar_fixed": True,
    "sidebar": "sidebar-dark-info",
    "sidebar_nav_small_text": True,
    "sidebar_disable_expand": True,
    "sidebar_nav_child_indent": True,
    "sidebar_nav_compact_style": True,
    "sidebar_nav_legacy_style": True,
    "sidebar_nav_flat_style": True,
    "sticky_actions": True,
    "actions_sticky_top": True,
    "theme": "lux",
    'hide_app': True,
    'hide_title': True,
    'show_logout': True,
    'show_user_avatar': True,
    "dark_mode_theme": None,
}

from datetime import timedelta

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(days=100),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=1),
    "SIGNING_KEY": SECRET_KEY,
}

from cryptography.fernet import Fernet

# Генерируем один раз и сохраняем
# 🔑 Ключ шифрования Fernet (32 байта, base64)
# Сгенерирован один раз и теперь постоянный
FERNET_KEY = b'Vq6xo6Cz6KXoTq8g7J1Q4bWlHkNz5G7I4B9xP3cR2sI='

from decouple import config

# Рекомендуется задать отдельно:
# ENCRYPTION_KEY в виде base64 строки длиной 44 символа (для 32 байт -> base64 = 44 chars)
# Генерация примера: python -c "import base64, os; print(base64.b64encode(os.urandom(32)).decode())"
ENCRYPTION_KEY = config("ENCRYPTION_KEY", default=None)  # используется в crypto.get_encryption_key()

# Безопасные cookie/https настройки (для продакшн)
SECURE_SSL_REDIRECT = config("SECURE_SSL_REDIRECT", default=True, cast=bool)
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
X_FRAME_OPTIONS = "DENY"
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
