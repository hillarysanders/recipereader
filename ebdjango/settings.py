"""
Django settings for ebdjango project.

Generated by 'django-admin startproject' using Django 1.9.2.

For more information on this file, see
https://docs.djangoproject.com/en/1.9/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/1.9/ref/settings/
"""

import os

try:
    from .credentials import *
except ImportError:
    pass
# now creds should be environments variables (either from .credentials or aws elasticbeanstalk)
AWS_S3_ACCESS_KEY_ID = os.environ['AWS_S3_ACCESS_KEY_ID']
AWS_S3_SECRET_ACCESS_KEY = os.environ['AWS_S3_SECRET_ACCESS_KEY']
AWS_STORAGE_BUCKET_NAME = os.environ['AWS_STORAGE_BUCKET_NAME']
SECRET_KEY = os.environ['SECRET_KEY']


# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/1.9/howto/deployment/checklist/

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = False

ALLOWED_HOSTS = ['127.0.0.1', 'localhost', 'www.recipestasher.com', 'recipestasher.com']

# Application definition

# STATICFILES_DIRS = [
#     os.path.join(BASE_DIR, "static"),
#     os.path.join(BASE_DIR, "static/materialize/"),
# ]

# note: the migrate command will only run migrations (create database tables) for apps in INSTALLED_APPS:
INSTALLED_APPS = [
    # all of these come with django by default
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.sites',
    # postgres search:
    'django.contrib.postgres',
    # materialize form helper: (awesome: https://github.com/florent1933/django-materializecss-form)
    'materialize_forms',
    'storages',
    # 'captcha',
    # homemade apps:
    'polls.apps.PollsConfig',
    'home.apps.HomeConfig'
]
DEFAULT_FILE_STORAGE = 'storages.backends.s3boto.S3BotoStorage'

MIDDLEWARE_CLASSES = [
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.auth.middleware.SessionAuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'ebdjango.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'home/templates')],  # just home templates
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                # this line is so we can use MEDIA_URL in templates:
                'django.template.context_processors.media',
            ],
        },
    },
]


WSGI_APPLICATION = 'ebdjango.wsgi.application'


# Database
# https://docs.djangoproject.com/en/1.9/ref/settings/#databases
x = """
from db import DB
conn = DB(dbtype='postgres',
          dbname='{}',
          username='{}',
          password='{}',
          hostname='{}')
          """.format(os.environ['DB_NAME'],
                     os.environ['DB_USER'],
                     os.environ['DB_PASSWORD'],
                     os.environ['DB_HOST'])

DATABASES = {
    'default': {
        'ENGINE': os.environ['DB_ENGINE'],
        'NAME': os.environ['DB_NAME'],
        'USER': os.environ['DB_USER'],  # admin or hills?
        'PASSWORD': os.environ['DB_PASSWORD'],
        'HOST': os.environ['DB_HOST'],
        'PORT': os.environ['DB_PORT'],
        # adding this options.init_command line so that user <--> recipe relationships don't break things...?
        # 'OPTIONS': {
        #  "init_command": "SET foreign_key_checks = 0;",
        # },
    }
}

AUTHENTICATION_BACKENDS = (
    ('django.contrib.auth.backends.ModelBackend'),
)

# Password validation
# https://docs.djangoproject.com/en/1.9/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    # because fuck password validation <3
    # {
    #     'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    # },
    # {
    #     'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    # },
    # {
    #     'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    # },
    # {
    #     'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    # },
]

# cloudinary.config(
#   cloud_name = "dkw0dtp8h",
#   api_key = "632629697964542",
#   api_secret = "5TR-RWm4g5v_mZRkEtzSnmT1qV4"
# )


# Internationalization
# https://docs.djangoproject.com/en/1.9/topics/i18n/
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'US/Pacific'
USE_I18N = True
USE_L10N = True
USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.9/howto/static-files/
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, '..', 'static')

# if not DEBUG:
# # #     AWS_STORAGE_BUCKET_NAME = 'bw-pngs'
# # #     AWS_ACCESS_KEY_ID = AWS_S3_ACCESS_KEY_ID
# # #     AWS_SECRET_ACCESS_KEY = AWS_S3_SECRET_ACCESS_KEY
#     STATICFILES_STORAGE = 'storages.backends.s3boto.S3BotoStorage'
#     STATIC_S3_URL = 'https://s3-us-west-2.amazonaws.com/recipereader-user-images/static/'
#     STATIC_URL = STATIC_S3_URL
#     STATIC_ROOT = STATIC_S3_URL
#     # todo fix this


MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, '..', 'media')

# MEDIA_ROOT = '/Users/hills/Desktop/code/django-beanstalk/ebdjango/media/'
# MEDIA_ROOT = '/media/'
# MEDIA_URL = '/media/'
# MEDIA_URL = "https://recipereader-user-images.s3-us-west-2.amazonaws.com/"

# SESSION_ENGINE = "django.contrib.sessions.backends.signed_cookies"
# SESSION_COOKIE_HTTPONLY = True
# SESSION_SAVE_EVERY_REQUEST = True

LOGIN_URL = '/'
SESSION_COOKIE_AGE = 604800  # 1 week, in seconds

# CAPTCHA_NOISE_FUNCTIONS = []
# CAPTCHA_MATH_CHALLENGE_OPERATOR = ['x']
# CAPTCHA_CHALLENGE_FUNCT = 'captcha.helpers.math_challenge'

# SECURE_CONTENT_TYPE_NOSNIFF = True
# SECURE_BROWSER_XSS_FILTER = True
# SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = True
# CSRF_COOKIE_HTTPONLY = True
# X_FRAME_OPTIONS = 'DENY'
# performance optimization:
CONN_MAX_AGE = 600  # 0 = wait and then close

# CSRF_COOKIE_DOMAIN  = '.recipestasher.com'
# CSRF_TRUSTED_ORIGINS = ['.recipestasher.com']
# CSRF_FAILURE_VIEW = 'home.views.csrf_failure'