# Django settings for example project.

import os

DEBUG = TEMPLATE_DEBUG = True

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': 'example.db',
    }
}

SECRET_KEY = '=&$4-fziwu=^k0#2-w+r#%3+v2*oc%#!1l2%&_h1*hp&a5zbav'

ROOT_URLCONF = 'example.urls'

INSTALLED_APPS = (
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.messages',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django_storymarket',
    'example',
)
TEMPLATE_DIRS = []

# Storymarket settings
STORYMARKET_API_KEY = os.environ['STORYMARKET_API_KEY']