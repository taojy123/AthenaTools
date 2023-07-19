
# coding=utf-8
# Django settings for athenatools project.
import os
import uuid

import pymysql


pymysql.install_as_MySQLdb()


# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

DEBUG = True

LOGIN_URL = '/login/'

ALLOWED_HOSTS = ['*']

ADMINS = (
    ('taojy123', 'taojy123@163.com'),
)

MANAGERS = ADMINS

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql', # Add 'postgresql_psycopg2', 'mysql', 'sqlite3' or 'oracle'.
        'NAME': 'athenatools',                      # Or path to database file if using sqlite3.
        'USER': 'athenatools',                      # Not used with sqlite3.
        'PASSWORD': '',                  # Not used with sqlite3.
        'HOST': 'tools.athenagu.com',                      # Set to empty string for localhost. Not used with sqlite3.
        'PORT': '3306',                      # Set to empty string for default. Not used with sqlite3.
        'OPTIONS': {'charset': 'utf8mb4'},   # for emoji at mysql
    }
}

SITE_ID = 1

# Internationalization
# https://docs.djangoproject.com/en/1.9/topics/i18n/

LANGUAGE_CODE = 'zh-Hans'

TIME_ZONE = 'Asia/Shanghai'

USE_I18N = True

USE_L10N = False

USE_TZ = True


# USE_L10N must be False, below will work
DATE_FORMAT = 'Y-m-d'
DATETIME_FORMAT = 'Y-m-d H:i'
# DATE_FORMAT = 'j E Y r.'
# TIME_FORMAT = 'G:i'
# DATETIME_FORMAT = 'j E Y г. G:i'
# YEAR_MONTH_FORMAT = 'F Y г.'
# MONTH_DAY_FORMAT = 'j F'
# SHORT_DATE_FORMAT = 'd.m.Y'
# SHORT_DATETIME_FORMAT = 'd.m.Y H:i'


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.9/howto/static-files/

STATICFILES_DIRS = [os.path.join(BASE_DIR, 'static')]

STATIC_ROOT = './staticroot/'
STATIC_URL = '/static/'


# Absolute filesystem path to the directory that will hold user-uploaded files.
# Example: "/home/media/media.lawrence.com/media/"
MEDIA_ROOT = './static/media/'

# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash.
# Examples: "http://media.lawrence.com/media/", "http://example.com/media/"
MEDIA_URL = '/static/media/'


# List of finder classes that know how to find static files in
# various locations.
STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
#    'django.contrib.staticfiles.finders.DefaultStorageFinder',
)

# Make this unique, and don't share it with anybody.
SECRET_KEY = 'django-quickstart-1ac3a4e1-c6ef-4985-96f8-81d075cc7c3f'

MIDDLEWARE_CLASSES = (
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    #'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    # Uncomment the next line for simple clickjacking protection:
    # 'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'corsheaders.middleware.CorsMiddleware',
)

ROOT_URLCONF = 'athenatools.urls'

# Python dotted path to the WSGI application used by Django's runserver.
WSGI_APPLICATION = 'athenatools.wsgi.application'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')],
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

INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.admin',
    'corsheaders',
    'qiniustorage',
    'lazypage',
    'athenatools',
)

# A sample logging configuration. The only tangible logging
# performed by this configuration is to send an email to
# the site admins on every HTTP 500 error when DEBUG=False.
# See http://docs.djangoproject.com/en/dev/topics/logging for
# more details on how to customize your logging configuration.
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'filters': {
        'require_debug_false': {
            '()': 'django.utils.log.RequireDebugFalse'
        },
        'require_debug_true': {
            '()': 'django.utils.log.RequireDebugTrue'
        }
    },
    'handlers': {
        'mail_admins': {
            'level': 'ERROR',
            'filters': ['require_debug_false'],
            'class': 'django.utils.log.AdminEmailHandler'
        },
        'console': {
            'level': 'DEBUG',
            'filters': ['require_debug_true'],
            'class': 'logging.StreamHandler',
        },
    },
    'loggers': {
        'django.request': {
            'handlers': ['mail_admins'],
            'level': 'ERROR',
            'propagate': False,
        },
        # 'django.db.backends': {
        #     'handlers': ['console'],
        #     'level': 'DEBUG',
        #     'propagate': True,
        # },
    }
}


DATA_UPLOAD_MAX_MEMORY_SIZE = 50 * 1024 * 1024  # 50MB


SERVER_EMAIL = 'watchmen123456@163.com'
EMAIL_HOST = 'smtp.163.com'
EMAIL_PORT = 465
EMAIL_USE_SSL = True
EMAIL_HOST_USER = 'watchmen123456'
EMAIL_HOST_PASSWORD = ''
EMAIL_SUBJECT_PREFIX = '[athenatools] '


# CORS
CORS_ORIGIN_ALLOW_ALL = False
CORS_ALLOW_CREDENTIALS = True
CORS_ALLOWED_ORIGINS = [
    "https://manage-test.diyiedu.com",
    "https://manage.diyiedu.com",
    "http://localhost:10000",
]
CORS_ALLOW_HEADERS = [
    'x-requested-with',
    'content-type',
    'accept',
    'origin',
    'authorization',
    'cache-control',
    'x-http-method-override',
    'x-bulk-operation',
    'x-frame-options',
]


LAZYPAGE = {
    'EXPIRED_SECONDS': 3600,
    'POLLING_SECONDS': 3,
    'ASYNC_BY_CELERY': False,
    'STORE_BY_REDIS': False,
}


# Qiniu
DEFAULT_FILE_STORAGE = 'qiniustorage.backends.QiniuStorage'
QINIU_ACCESS_KEY = ''
QINIU_SECRET_KEY = ''
QINIU_BUCKET_NAME = 'athena'
QINIU_BUCKET_DOMAIN = 'qiniu.athenagu.com'
QINIU_SECURE_URL = False



try:
    from .local_settings import *
except ImportError:
    pass


if not DEBUG:
    STATIC_URL = 'https://cdn.tslow.cn/AthenaTools/static/'

