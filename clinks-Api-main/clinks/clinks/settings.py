"""
Django settings for clinks project.

Generated by 'django-admin startproject' using Django 4.0.1.

For more information on this file, see
https://docs.djangoproject.com/en/4.0/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/4.0/ref/settings/
"""

from pathlib import Path
from tempfile import NamedTemporaryFile
import os, datetime, atexit, sys

# GDAL_LIBRARY_PATH = '/opt/homebrew/Cellar/gdal/3.9.3_1/lib/libgdal.dylib'
# GEOS_LIBRARY_PATH = '/opt/homebrew/Cellar/geos/3.13.0/lib/libgeos_c.dylib'

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/4.0/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.environ['GENERAL_SECRET_KEY']

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.environ['GENERAL_DEBUG'] == 'True'

ALLOWED_HOSTS = [os.environ['GENERAL_HOST_DOMAIN'], '127.0.0.1', 'localhost']

APPEND_SLASH = False

SECURE_SSL_REDIRECT = not DEBUG

# Application definition

INSTALLED_APPS = [
    'rest_framework',
    'rest_framework_simplejwt.token_blacklist',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'corsheaders',
    'push_notifications',
    'api',
    'celery'
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'api.middleware.LastSeen',
    'api.middleware.Logging',
    'api.utils.logging_middleware.LogPushNotificationRequestsMiddleware',
]

CORS_ORIGIN_ALLOW_ALL = True

ROOT_URLCONF = 'clinks.urls'

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

WSGI_APPLICATION = 'clinks.wsgi.application'


# Database
# https://docs.djangoproject.com/en/4.0/ref/settings/#databases

default_db = {
    'ENGINE': os.environ['DATABASE_ENGINE'],
    'NAME': os.environ['DATABASE_NAME'],
    'USER': os.environ['DATABASE_USER'],
    'PASSWORD': os.environ['DATABASE_PASSWORD'],
    'HOST': os.environ['DATABASE_HOST'],
    'PORT': os.environ['DATABASE_PORT'],
}

if "CI" in os.environ and os.environ['CI'] == "true":
    import dj_database_url
    default_db = dj_database_url.parse(os.environ['DATABASE_URL'], conn_max_age=600)
    default_db['ENGINE'] = os.environ['DATABASE_ENGINE']

default_db["TEST"] = {
    # CI_NODE_INDEX ignored if not available, such as when performing a local build
    # ensures parallel tests use different databases
    'NAME': 'test_clinks_' + os.getenv('CI_NODE_INDEX', "local")
}

DATABASES = {
    'default': default_db
}


# Password validation
# https://docs.djangoproject.com/en/4.0/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
        'OPTIONS': {
            'min_length': 6,
        }
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'api.utils.PasswordValidation.NumberValidator'
    },
    {
        'NAME': 'api.utils.PasswordValidation.UppercaseValidator'
    },
    {
        'NAME': 'api.utils.PasswordValidation.LowercaseValidator'
    },
    {
        'NAME': 'api.utils.PasswordValidation.SpecialCharacterValidator'
    }
]


# Internationalization
# https://docs.djangoproject.com/en/4.0/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/4.0/howto/static-files/

STATIC_URL = 'static/'

# Default primary key field type
# https://docs.djangoproject.com/en/4.0/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

AUTH_USER_MODEL = 'api.User'

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': datetime.timedelta(weeks=2),
    'REFRESH_TOKEN_LIFETIME': datetime.timedelta(weeks=52),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True
}

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
        'rest_framework.authentication.SessionAuthentication',
        'rest_framework.authentication.BasicAuthentication',
    ),
    'DEFAULT_PARSER_CLASSES': (
        'rest_framework.parsers.JSONParser',
        'rest_framework.parsers.FormParser',
        'rest_framework.parsers.MultiPartParser',
        'rest_framework.parsers.FileUploadParser',
    ),
}

ADMINS = [("begum", "begum@mosaic.ie")]
EMAIL_HOST = "smtp.sendgrid.net"
EMAIL_HOST_USER = "apikey"
EMAIL_HOST_PASSWORD = os.environ['SENDGRID_API_KEY']
EMAIL_PORT = 587
EMAIL_USE_TLS = True
SERVER_EMAIL = "www.clinks.ie@gmail.com"

# Celery - controls the background/async tasks used
CELERY_BROKER_URL = os.environ['BROKER_URL']

# celery - makes tasks synchronous for tests/local when DEBUG is true
CELERY_TASK_ALWAYS_EAGER = DEBUG

TEST_RUNNER = 'api.test_runner.ProfileTestRunner'

apns_file = NamedTemporaryFile(delete=False)
apns_file.write(bytes(os.environ['APNS_AUTH_KEY'], 'UTF-8'))
apns_file.close()
apns_file_name = apns_file.name


def unlink_file():
    os.unlink(apns_file_name)


atexit.register(unlink_file)

PUSH_NOTIFICATIONS_SETTINGS = {
    "FCM_API_KEY": os.environ['FCM_API_KEY'],
    "FCM_POST_URL": "https://fcm.googleapis.com/v1/projects/clinks-1f1c7/messages:send",
    "APNS_AUTH_KEY_PATH": apns_file_name,
    "APNS_AUTH_KEY_ID": os.environ["APNS_AUTH_KEY_ID"],
    "APNS_TEAM_ID": os.environ["APPLE_TEAM_ID"],
    "APNS_TOPIC": os.environ['APPLE_CLIENT_ID'],
    "APNS_USE_SANDBOX": os.environ['PUSH_NOTIFICATION_IN_DEBUG'] == 'True',
    "UPDATE_ON_DUPLICATE_REG_ID": True
}

TESTING = len(sys.argv) > 1 and sys.argv[1] == 'test'

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'WARNING',
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': os.getenv('DJANGO_LOG_LEVEL', 'WARNING'),
            'propagate': True,  # Allow propagation of 'django.request' logs
        },
        '__main__': {
            'handlers': ['console'],
            'level': 'ERROR',
        },
        'clinks-api-live': {
            'handlers': ['console'],
            'level': 'DEBUG',
            'propagate': True,
        },
    },
}