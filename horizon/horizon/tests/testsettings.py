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

import os
import socket

socket.setdefaulttimeout(1)

ROOT_PATH = os.path.dirname(os.path.abspath(__file__))
DEBUG = True
TESTSERVER = 'http://testserver'
DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': '/tmp/horizon.db',
            'TEST_NAME': '/tmp/test_horizon.db'}}

INSTALLED_APPS = (
    'django.contrib.sessions',
    'django.contrib.messages',
    'django_nose',
    'horizon',
    'horizon.tests',
    'horizon.dashboards.nova',
    'horizon.dashboards.syspanel',
    'horizon.dashboards.settings')

MIDDLEWARE_CLASSES = (
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.doc.XViewMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'horizon.middleware.HorizonMiddleware')

TEMPLATE_CONTEXT_PROCESSORS = (
    'django.core.context_processors.debug',
    'django.core.context_processors.i18n',
    'django.core.context_processors.request',
    'django.core.context_processors.media',
    'django.core.context_processors.static',
    'django.contrib.messages.context_processors.messages',
    'horizon.context_processors.horizon')

ROOT_URLCONF = 'horizon.tests.testurls'
TEMPLATE_DIRS = (os.path.join(ROOT_PATH, 'tests', 'templates'))
SITE_ID = 1
SITE_BRANDING = 'OpenStack'
SITE_NAME = 'openstack'
ENABLE_VNC = True
NOVA_DEFAULT_ENDPOINT = None
NOVA_DEFAULT_REGION = 'test'
NOVA_ACCESS_KEY = 'test'
NOVA_SECRET_KEY = 'test'

QUANTUM_URL = '127.0.0.1'
QUANTUM_PORT = '9696'
QUANTUM_TENANT = '1234'
QUANTUM_CLIENT_VERSION = '0.1'
QUANTUM_ENABLED = True

CREDENTIAL_AUTHORIZATION_DAYS = 2
CREDENTIAL_DOWNLOAD_URL = TESTSERVER + '/credentials/'

TEST_RUNNER = 'django_nose.NoseTestSuiteRunner'
NOSE_ARGS = ['--nocapture',
             '--cover-package=horizon',
             '--cover-inclusive']
# For nose-selenium integration
LIVE_SERVER_PORT = 8000

EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'
SESSION_ENGINE = 'django.contrib.sessions.backends.cache'

HORIZON_CONFIG = {
    'dashboards': ('nova', 'syspanel', 'settings',),
    'default_dashboard': 'nova',
}

SWIFT_ACCOUNT = 'test'
SWIFT_USER = 'tester'
SWIFT_PASS = 'testing'
SWIFT_AUTHURL = 'http://swift/swiftapi/v1.0'

AVAILABLE_REGIONS = [
    ('local', 'http://localhost:5000/v2.0'),
    ('remote', 'http://remote:5000/v2.0'),
]

OPENSTACK_ADDRESS = "localhost"
OPENSTACK_ADMIN_TOKEN = "openstack"
OPENSTACK_KEYSTONE_URL = "http://%s:5000/v2.0" % OPENSTACK_ADDRESS
OPENSTACK_KEYSTONE_ADMIN_URL = "http://%s:35357/v2.0" % OPENSTACK_ADDRESS
OPENSTACK_KEYSTONE_DEFAULT_ROLE_ID = "2"

# Silence logging output during tests.
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'null': {
            'level': 'DEBUG',
            'class': 'django.utils.log.NullHandler',
            },
        },
    'loggers': {
        'django.db.backends': {
            'handlers': ['null'],
            'propagate': False,
            },
        'horizon': {
            'handlers': ['null'],
            'propagate': False,
        },
        'novaclient': {
            'handlers': ['null'],
            'propagate': False,
        },
        'keystoneclient': {
            'handlers': ['null'],
            'propagate': False,
        },
        'quantum': {
            'handlers': ['null'],
            'propagate': False,
        },
        'nose.plugins.manager': {
            'handlers': ['null'],
            'propagate': False,
        }
    }
}
