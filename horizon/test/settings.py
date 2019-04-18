# Copyright 2012 United States Government as represented by the
# Administrator of the National Aeronautics and Space Administration.
# All Rights Reserved.
#
# Copyright 2012 Nebula, Inc.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

import os
import socket

from horizon.defaults import *  # noqa: F403,H303
from openstack_auth.defaults import *  # noqa: F403,H303
from openstack_dashboard.utils import settings as settings_utils

socket.setdefaulttimeout(1)

LOGIN_URL = '/auth/login/'
LOGIN_REDIRECT_URL = '/'

ROOT_PATH = os.path.dirname(os.path.abspath(__file__))
STATIC_ROOT = os.path.abspath(os.path.join(ROOT_PATH, '..', 'static'))

DEBUG = False
TESTSERVER = 'http://testserver'

SECRET_KEY = 'elj1IWiLoWHgcyYxFVLj7cM5rGOOxWl0'

USE_I18N = True
USE_L10N = True
USE_TZ = True

DATABASES = {'default': {'ENGINE': 'django.db.backends.sqlite3'}}

DEFAULT_EXCEPTION_REPORTER_FILTER = 'horizon.exceptions.HorizonReporterFilter'

INSTALLED_APPS = (
    'django.contrib.sessions',
    'django.contrib.staticfiles',
    'django.contrib.messages',
    'django.contrib.humanize',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django_pyscss',
    'compressor',
    'horizon',
    'horizon.test',
    'horizon.test.test_dashboards.cats',
    'horizon.test.test_dashboards.dogs',
    'openstack_auth'
)

MIDDLEWARE = (
    'openstack_auth.middleware.OpenstackAuthMonkeyPatchMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'horizon.middleware.HorizonMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
)

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(ROOT_PATH, 'tests', 'templates')],
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.i18n',
                'django.template.context_processors.request',
                'django.template.context_processors.media',
                'django.template.context_processors.static',
                'django.contrib.messages.context_processors.messages',
                'horizon.context_processors.horizon',
            ],
            'debug': True,
            'loaders': [
                'django.template.loaders.filesystem.Loader',
                'django.template.loaders.app_directories.Loader',
                'horizon.loaders.TemplateLoader'
            ],
        },
    },
]

STATIC_URL = '/static/'

MESSAGE_STORAGE = 'django.contrib.messages.storage.cookie.CookieStorage'

ROOT_URLCONF = 'horizon.test.urls'
SITE_ID = 1

EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'
SESSION_ENGINE = 'django.contrib.sessions.backends.signed_cookies'
SESSION_COOKIE_HTTPONLY = True
SESSION_EXPIRE_AT_BROWSER_CLOSE = True
SESSION_COOKIE_SECURE = False

HORIZON_CONFIG = {
    'dashboards': ('cats', 'dogs'),
    'default_dashboard': 'cats',
    "password_validator": {
        "regex": '^.{8,18}$',
        "help_text": "Password must be between 8 and 18 characters."
    },
    'user_home': None,
    'bug_url': None,
    'help_url': "http://example.com",
}

STATICFILES_DIRS = settings_utils.get_xstatic_dirs(
    settings_utils.BASE_XSTATIC_MODULES, HORIZON_CONFIG
)

COMPRESS_ENABLED = True
COMPRESS_OFFLINE = False
COMPRESS_ROOT = "/tmp/"
COMPRESS_PARSER = 'compressor.parser.HtmlParser'

STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'horizon.contrib.staticfiles.finders.HorizonStaticFinder',
    'compressor.finders.CompressorFinder',
)

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'null': {
            'level': 'DEBUG',
            'class': 'logging.NullHandler',
        },
        'test': {
            'level': 'ERROR',
            'class': 'logging.StreamHandler',
        }
    },
    'loggers': {
        'django.db.backends': {
            'handlers': ['null'],
            'propagate': False,
        },
        'horizon': {
            'handlers': ['test'],
            'propagate': False,
        },
        'selenium': {
            'handlers': ['null'],
            'propagate': False,
        }
    }
}
