# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright 2011 United States Government as represented by the
# Administrator of the National Aeronautics and Space Administration.
# All Rights Reserved.
#
# Copyright 2011 Nebula, Inc.
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

import logging
import os
import sys

ROOT_PATH = os.path.dirname(os.path.abspath(__file__))

sys.path.append(ROOT_PATH)

DEBUG = False
TEMPLATE_DEBUG = DEBUG

SITE_ID = 1
SITE_BRANDING = 'OpenStack'
SITE_NAME = 'openstack'
ENABLE_VNC = True

LOGIN_URL = '/auth/login'
LOGIN_REDIRECT_URL = '/'

MEDIA_ROOT = os.path.abspath(os.path.join(ROOT_PATH, '..', 'media'))
MEDIA_URL = '/media/'
STATIC_ROOT = os.path.abspath(os.path.join(ROOT_PATH, '..', 'static'))
STATIC_URL = '/static/'
ADMIN_MEDIA_PREFIX = '/static/admin/'

CREDENTIAL_AUTHORIZATION_DAYS = '5'

ROOT_URLCONF = 'dashboard.urls'

MIDDLEWARE_CLASSES = (
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django_openstack.middleware.keystone.AuthenticationMiddleware',
    'django.middleware.doc.XViewMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'dashboard.middleware.DashboardLogUnhandledExceptionsMiddleware',
)

TEMPLATE_CONTEXT_PROCESSORS = (
    'django.core.context_processors.debug',
    'django.core.context_processors.i18n',
    'django.core.context_processors.request',
    'django.core.context_processors.media',
    'django.core.context_processors.static',
    'django.contrib.messages.context_processors.messages',
    'django_openstack.context_processors.swift',
    'django_openstack.context_processors.tenants',
    'django_openstack.context_processors.quantum',
)

TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.load_template_source',
    'django.template.loaders.app_directories.load_template_source',
)

TEMPLATE_DIRS = (
    os.path.join(ROOT_PATH, 'templates'),
)

STATICFILES_DIRS = (
    os.path.join(ROOT_PATH, 'static'),
)

INSTALLED_APPS = (
    'dashboard',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django_openstack',
    'django_openstack.templatetags',
    'mailer',
)

TEST_RUNNER = 'django_nose.NoseTestSuiteRunner'
AUTHENTICATION_BACKENDS = ('django.contrib.auth.backends.ModelBackend',)
MESSAGE_STORAGE = 'django.contrib.messages.storage.cookie.CookieStorage'

SESSION_EXPIRE_AT_BROWSER_CLOSE = True
TIME_ZONE = None
gettext_noop = lambda s: s
LANGUAGES = (
    ('en', gettext_noop('English')),
    ('en-gb', gettext_noop('British English')),
    ('it', gettext_noop('Italiano')),
    ('es', gettext_noop('Spanish')),
    ('fr', gettext_noop('French')),
    ('ja', gettext_noop('Japanese')),
    ('pt', gettext_noop('Portuguese')),
    ('zh-cn', gettext_noop('Simplified Chinese')),
    ('zh-tw', gettext_noop('Traditional Chinese')),
)
LANGUAGE_CODE = 'en'
USE_I18N = True

ACCOUNT_ACTIVATION_DAYS = 7

TOTAL_CLOUD_RAM_GB = 10

try:
    from local.local_settings import *
except Exception, e:
    logging.exception(e)

if DEBUG:
    logging.basicConfig(level=logging.DEBUG)

    try:
        import debug_toolbar

        INSTALLED_APPS += ('debug_toolbar',)
        MIDDLEWARE_CLASSES += (
                'debug_toolbar.middleware.DebugToolbarMiddleware',)
    except ImportError:
        logging.info('Running in debug mode without debug_toolbar.')

OPENSTACK_KEYSTONE_DEFAULT_ROLE = 'Member'
