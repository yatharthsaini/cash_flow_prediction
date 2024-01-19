"""
Django settings for cash_flow_prediction project.

Generated by 'django-admin startproject' using Django 4.2.4.

For more information on this file, see
https://docs.djangoproject.com/en/4.2/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/4.2/ref/settings/
"""

from pathlib import Path
import os
from celery import Celery
from corsheaders.defaults import default_headers
from dotenv import load_dotenv
from utils.constants import MethodNames


load_dotenv()  # take environment variables from .env

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/4.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.environ.get('SECRET_KEY')

# ENVIRONMENT
ENVIRONMENT = os.environ.get('ENVIRONMENT')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.environ.get('DEBUG')

ALLOWED_HOSTS = os.environ.get("ALLOWED_HOSTS", "").split()
CSRF_TRUSTED_ORIGINS = os.environ.get("CSRF_TRUSTED_ORIGINS", "").split()

# application definition
ROOT_APP = ["cash_flow_prediction"]

# core django apps
DJANGO_CORE_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
]

# third party apps used in the project
THIRD_PARTY_APPS = [
    "rest_framework",
    "corsheaders",
    'rest_framework_swagger',
    'drf_spectacular',
    'django_celery_beat',
    'django_celery_results',
    'debug_toolbar'
]

SERVER_APP = ["cash_flow"]

INSTALLED_APPS = DJANGO_CORE_APPS + THIRD_PARTY_APPS + ROOT_APP + SERVER_APP

# default django middleware
DJANGO_MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

THIRD_PARTY_MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
]

MIDDLEWARE = DJANGO_MIDDLEWARE + THIRD_PARTY_MIDDLEWARE

if DEBUG:
    MIDDLEWARE += ['debug_toolbar.middleware.DebugToolbarMiddleware']

    SPECTACULAR_SETTINGS = {
        "TITLE": "cash_flow_prediction",
        "DESCRIPTION": "Cash flow prediction API's",
        "VERSION": "1.0.0",
        "SWAGGER_UI_DIST": "SIDECAR",  # shorthand to use the sidecar instead
        "SWAGGER_UI_FAVICON_HREF": "SIDECAR",
        "REDOC_DIST": "SIDECAR",
    }

    DEBUG_TOOLBAR_PANELS = [
        'debug_toolbar.panels.history.HistoryPanel',
        'debug_toolbar.panels.versions.VersionsPanel',
        'debug_toolbar.panels.timer.TimerPanel',
        'debug_toolbar.panels.settings.SettingsPanel',
        'debug_toolbar.panels.headers.HeadersPanel',
        'debug_toolbar.panels.request.RequestPanel',
        'debug_toolbar.panels.sql.SQLPanel',
        'debug_toolbar.panels.staticfiles.StaticFilesPanel',
        'debug_toolbar.panels.templates.TemplatesPanel',
        'debug_toolbar.panels.cache.CachePanel',
        'debug_toolbar.panels.signals.SignalsPanel',
        'debug_toolbar.panels.logging.LoggingPanel',
        'debug_toolbar.panels.redirects.RedirectsPanel',
        'debug_toolbar.panels.profiling.ProfilingPanel',
    ]
    DEBUG_TOOLBAR_CONFIG = {
        "SHOW_TOOLBAR_CALLBACK": lambda request: True,
    }

ROOT_URLCONF = 'cash_flow_prediction.urls'

# CORS Headers Settings
CORS_ALLOWED_ORIGINS = [
    "http://localhost:8080",
    "http://localhost:3000",
    "http://127.0.0.1:8000",
    "https://slugbuns.paymeindia.in"
]

# imported MethodNames enum from the constants.py
CORS_ALLOW_METHODS = [
    MethodNames.GET.value,
    MethodNames.POST.value,
    MethodNames.DELETE.value,
    MethodNames.PATCH.value,
    MethodNames.OPTIONS.value,
    MethodNames.HEAD.value,
]

CORS_ALLOW_HEADERS = default_headers

# templates default
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': ['templates'],
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

WSGI_APPLICATION = 'cash_flow_prediction.wsgi.application'
ASGI_APPLICATION = 'cash_flow_prediction.asgi.application'


# Database
# https://docs.djangoproject.com/en/4.2/ref/settings/#databases

# databases used in the django projects, creds to be fetched from .env
DATABASES = {
    "default": {
        "ENGINE": os.environ.get("POSTGRES_ENGINE"),
        "NAME": os.environ.get("POSTGRES_DB"),
        "USER": os.environ.get("POSTGRES_USER"),
        "PASSWORD": os.environ.get("POSTGRES_PASSWORD"),
        "HOST": os.environ.get("POSTGRES_HOST"),
        "PORT": os.environ.get("POSTGRES_PORT"),
    }
}

# rest framework
DEFAULT_PERMISSION_CLASS = [
    # "rest_framework.permissions.IsAuthenticated",
]

DEFAULT_AUTHENTICATION_CLASSES = [
    # "rest_framework.authentication.BasicAuthentication",
]

REST_FRAMEWORK = {
    "DEFAULT_PERMISSION_CLASSES": DEFAULT_PERMISSION_CLASS,
    "DEFAULT_AUTHENTICATION_CLASSES": DEFAULT_AUTHENTICATION_CLASSES,
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "DEFAULT_RENDERER_CLASSES": [
        "rest_framework.renderers.JSONRenderer",
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 100
}

# Password validation
# https://docs.djangoproject.com/en/4.2/ref/settings/#auth-password-validators

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
# https://docs.djangoproject.com/en/4.2/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'Asia/Kolkata'

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/4.2/howto/static-files/

STATIC_URL = "/static/"
MEDIA_URL = "/media/"
STATIC_ROOT = os.path.join(BASE_DIR / "static")
MEDIA_ROOT = os.path.join(BASE_DIR, "media_root")


# Default primary key field type
# https://docs.djangoproject.com/en/4.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# For running test cases...
TEST_RUNNER = "django.test.runner.DiscoverRunner"

# for authentication using paymeIndia auth apis
TOKEN_AUTHENTICATION_URL = os.environ.get('PAYME_BASE_URL') + os.environ.get('TOKEN_AUTHENTICATION_URL')

# Celery config
celery = Celery('cash_flow_prediction')
celery.config_from_object('')

CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": os.environ.get('REDIS_URL'),
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
        }
    }
}

# Redis instance
REDIS_URL = os.environ.get('REDIS_URL')

CELERY_BROKER_URL = os.environ.get("CELERY_BROKER_URL")
CELERY_RESULT_BACKEND = os.environ.get("CELERY_RESULT_BACKEND")
CELERY_RESULT_SERIALIZER = os.environ.get("CELERY_RESULT_SERIALIZER")
CELERY_CACHE_BACKEND = 'django-cache'

CELERY_TIMEZONE = "Asia/Kolkata"
CELERY_TASK_TRACK_STARTED = True
CELERY_RESULT_EXTENDED = True

# email settings ...
EMAIL_USE_TLS = os.environ.get("EMAIL_USE_TLS")
EMAIL_PORT = os.environ.get("EMAIL_PORT")
EMAIL_HOST = os.environ.get("EMAIL_HOST")
EMAIL_HOST_USER = os.environ.get("EMAIL_HOST_USER")
EMAIL_HOST_PASSWORD = os.environ.get("EMAIL_HOST_PASSWORD")
EMAIL_BACKEND = os.environ.get("EMAIL_BACKEND")
EMAIL_FROM = os.environ.get("EMAIL_FROM")
DEFAULT_FROM_EMAIL = os.environ.get("DEFAULT_FROM_EMAIL")
CELERY_ERROR_EMAIL_LIST = os.environ.get('CELERY_ERROR_EMAIL_LIST').split(" ")

SERVER_EMAIL = os.environ.get("SERVER_EMAIL")

# apis related to collection efficiency data
COLLECTION_PREDICTION_POLL_URL = os.environ.get('COLLECTION_PREDICTION_POLL_URL')
DUE_AMOUNT_URL = os.environ.get('DUE_AMOUNT_URL')
COLLECTION_PREDICTION_TOKEN = os.environ.get('COLLECTION_PREDICTION_TOKEN')
NBFC_LIST_URL = os.environ.get('NBFC_LIST_URL')
COLLECTION_AMOUNT_URL = os.environ.get('COLLECTION_AMOUNT_URL')
LOAN_BOOKED_URL = os.environ.get('LOAN_BOOKED_URL')
CASH_FLOW_URL = os.environ.get('CASH_FLOW_URL')
FAILED_LOAN_DATA = os.environ.get('FAILED_LOAN_DATA')

# Project Name
PROJECT_NAME = os.environ.get('PROJECT_NAME')

ADMINS = [
    ("Vineet", "vineet.daniel@paymeindia.in"),
    ("Alok", "alok.sharma@paymeindia.in"),
    ("Vishal", "gupta.vishal@paymeindia.in"),
    ("Satish", "satish.pandey@paymeindia.in"),
    ("Manit", "manit.choudhary@paymeindia.in"),
    ("Avinash", "avinash.kumar@paymeindia.in"),
    ("Vimal", "vimal.mahawar@paymeindia.in"),
    ("Parul", "parul@paymeindia.in"),
    ("Ankit", "ankit.baliyan@paymeindia.in"),
    ("Abhishek", "abhishek.gupta@paymeindia.in"),
    ("Yatharth", "yatharth.saini@paymeindia.in"),
    ("Aayush", "aayush.rawal@paymeindia.in"),
    ("Tarun", "tarun.pandey@paymeindia.in"),
    ("Dheeraj", "dheeraj.thakur@paymeindia.in"),
]

if ENVIRONMENT == "PRODUCTION":
    INSTALLED_APPS += ["elasticapm.contrib.django"]
    ELASTIC_APM = {
        "SERVICE_NAME": os.environ.get("APM_HOSTNAME"),
        'ENVIRONMENT': os.environ.get("ENVIRONMENT"),
        "DJANGO_TRANSACTION_NAME_FROM_ROUTE": True,
        'SERVER_URL': 'http://{}:{}'.format(os.environ.get("ELASTIC_APM_IP"), os.environ.get("ELASTIC_APM_PORT")),
    }

    MIDDLEWARE += [
        'elasticapm.contrib.django.middleware.TracingMiddleware',
    ]

    TEMPLATES[0]["OPTIONS"]["context_processors"] += ["elasticapm.contrib.django.context_processors.rum_tracing"]
