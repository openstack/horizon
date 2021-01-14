# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os

from openstack_auth.defaults import *  # noqa: F403,H303

ALLOWED_HOSTS = ['*']

DATABASES = {'default': {'ENGINE': 'django.db.backends.sqlite3'}}

INSTALLED_APPS = [
    'django',
    'django.contrib.contenttypes',
    'django.contrib.auth',
    'django.contrib.sessions',
    'django.contrib.messages',
    'openstack_auth',
    'openstack_auth.tests'
]

MIDDLEWARE = [
    'openstack_auth.middleware.OpenstackAuthMonkeyPatchMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware'
]

AUTHENTICATION_BACKENDS = ['openstack_auth.backend.KeystoneBackend']

ROOT_URLCONF = 'openstack_auth.tests.urls'

LOGIN_REDIRECT_URL = WEBROOT

SECRET_KEY = 'badcafe'

USE_TZ = True

OPENSTACK_KEYSTONE_DEFAULT_DOMAIN = 'domain'

# NOTE(saschpe): The openstack_auth.user.Token object isn't
# JSON-serializable ATM
SESSION_SERIALIZER = 'django.contrib.sessions.serializers.PickleSerializer'

TEST_DIR = os.path.dirname(os.path.abspath(__file__))
POLICY_FILES_PATH = os.path.join(TEST_DIR, "conf")
POLICY_FILES = {
    'identity': 'keystone_policy.json',
    'compute': 'nova_policy.json'
}

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'APP_DIRS': True,
    },
]

AUTH_USER_MODEL = 'openstack_auth.User'

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'test': {
            'level': 'ERROR',
            'class': 'logging.StreamHandler',
        }
    },
    'loggers': {
        'openstack_auth': {
            'handlers': ['test'],
            'propagate': False,
        },
    }
}
