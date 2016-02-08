# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

import os

from horizon.test.settings import *  # noqa
from horizon.utils import secret_key
from openstack_dashboard import exceptions
from openstack_dashboard.static_settings import find_static_files  # noqa
from openstack_dashboard.static_settings import get_staticfiles_dirs  # noqa

STATICFILES_DIRS = get_staticfiles_dirs()

TEST_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_PATH = os.path.abspath(os.path.join(TEST_DIR, ".."))
MEDIA_ROOT = os.path.abspath(os.path.join(ROOT_PATH, '..', 'media'))
MEDIA_URL = '/media/'
STATIC_ROOT = os.path.abspath(os.path.join(ROOT_PATH, '..', 'static'))
STATIC_URL = '/static/'
WEBROOT = '/'

SECRET_KEY = secret_key.generate_or_read_from_file(
    os.path.join(TEST_DIR, '.secret_key_store'))
ROOT_URLCONF = 'openstack_dashboard.test.urls'
TEMPLATE_DIRS = (
    os.path.join(TEST_DIR, 'templates'),
)

CUSTOM_THEME_PATH = 'themes/default'

TEMPLATE_CONTEXT_PROCESSORS += (
    'openstack_dashboard.context_processors.openstack',
)

COMPRESS_OFFLINE = False

INSTALLED_APPS = (
    'django.contrib.contenttypes',
    'django.contrib.auth',
    'django.contrib.sessions',
    'django.contrib.staticfiles',
    'django.contrib.messages',
    'django.contrib.humanize',
    'django_nose',
    'openstack_auth',
    'compressor',
    'horizon',
    'openstack_dashboard',
)

AUTHENTICATION_BACKENDS = ('openstack_auth.backend.KeystoneBackend',)

SITE_BRANDING = 'OpenStack'

HORIZON_CONFIG = {
    "password_validator": {
        "regex": '^.{8,18}$',
        "help_text": "Password must be between 8 and 18 characters."
    },
    'user_home': None,
    'help_url': "http://docs.openstack.org",
    'exceptions': {'recoverable': exceptions.RECOVERABLE,
                   'not_found': exceptions.NOT_FOUND,
                   'unauthorized': exceptions.UNAUTHORIZED},
    'angular_modules': [],
    'js_files': [],
}

# Load the pluggable dashboard settings
import openstack_dashboard.enabled
import openstack_dashboard.local.enabled
from openstack_dashboard.utils import settings

INSTALLED_APPS = list(INSTALLED_APPS)  # Make sure it's mutable
settings.update_dashboards(
    [
        openstack_dashboard.enabled,
        openstack_dashboard.local.enabled,
    ],
    HORIZON_CONFIG,
    INSTALLED_APPS,
)
INSTALLED_APPS[0:0] = []

find_static_files(HORIZON_CONFIG)

# Set to True to allow users to upload images to glance via Horizon server.
# When enabled, a file form field will appear on the create image form.
# See documentation for deployment considerations.
HORIZON_IMAGES_ALLOW_UPLOAD = True

AVAILABLE_REGIONS = [
    ('http://localhost:5000/v2.0', 'local'),
    ('http://remote:5000/v2.0', 'remote'),
]

OPENSTACK_API_VERSIONS = {
    "identity": 3
}

OPENSTACK_KEYSTONE_URL = "http://localhost:5000/v2.0"
OPENSTACK_KEYSTONE_DEFAULT_ROLE = "_member_"

OPENSTACK_KEYSTONE_MULTIDOMAIN_SUPPORT = True
OPENSTACK_KEYSTONE_DEFAULT_DOMAIN = 'test_domain'
OPENSTACK_KEYSTONE_FEDERATION_MANAGEMENT = True

OPENSTACK_KEYSTONE_BACKEND = {
    'name': 'native',
    'can_edit_user': True,
    'can_edit_group': True,
    'can_edit_project': True,
    'can_edit_domain': True,
    'can_edit_role': True
}

OPENSTACK_CINDER_FEATURES = {
    'enable_backup': True,
}

OPENSTACK_NEUTRON_NETWORK = {
    'enable_router': True,
    'enable_quotas': False,  # Enabled in specific tests only
    # Parameters below (enable_lb, enable_firewall, enable_vpn)
    # control if these panels are displayed or not,
    # i.e. they only affect the navigation menu.
    # These panels are registered even if enable_XXX is False,
    # so we don't need to set them to True in most unit tests
    # to avoid stubbing neutron extension check calls.
    'enable_lb': False,
    'enable_firewall': False,
    'enable_vpn': False,
    'profile_support': None,
    'enable_distributed_router': False,
    # 'profile_support': 'cisco'
}

OPENSTACK_HYPERVISOR_FEATURES = {
    'can_set_mount_point': False,
    'can_set_password': True,
}

OPENSTACK_IMAGE_BACKEND = {
    'image_formats': [
        ('', 'Select format'),
        ('aki', 'AKI - Amazon Kernel Image'),
        ('ami', 'AMI - Amazon Machine Image'),
        ('ari', 'ARI - Amazon Ramdisk Image'),
        ('iso', 'ISO - Optical Disk Image'),
        ('qcow2', 'QCOW2 - QEMU Emulator'),
        ('raw', 'Raw'),
        ('vdi', 'VDI'),
        ('vhd', 'VHD'),
        ('vmdk', 'VMDK')
    ]
}

LOGGING['loggers'].update(
    {
        'openstack_dashboard': {
            'handlers': ['test'],
            'propagate': False,
        },
        'openstack_auth': {
            'handlers': ['test'],
            'propagate': False,
        },
        'novaclient': {
            'handlers': ['test'],
            'propagate': False,
        },
        'keystoneclient': {
            'handlers': ['test'],
            'propagate': False,
        },
        'glanceclient': {
            'handlers': ['test'],
            'propagate': False,
        },
        'neutronclient': {
            'handlers': ['test'],
            'propagate': False,
        },
        'iso8601': {
            'handlers': ['null'],
            'propagate': False,
        },
    }
)

SECURITY_GROUP_RULES = {
    'all_tcp': {
        'name': 'ALL TCP',
        'ip_protocol': 'tcp',
        'from_port': '1',
        'to_port': '65535',
    },
    'http': {
        'name': 'HTTP',
        'ip_protocol': 'tcp',
        'from_port': '80',
        'to_port': '80',
    },
}

NOSE_ARGS = ['--nocapture',
             '--nologcapture',
             '--cover-package=openstack_dashboard',
             '--cover-inclusive',
             '--all-modules']

POLICY_FILES_PATH = os.path.join(ROOT_PATH, "conf")
POLICY_FILES = {
    'identity': 'keystone_policy.json',
    'compute': 'nova_policy.json'
}

# The openstack_auth.user.Token object isn't JSON-serializable ATM
SESSION_SERIALIZER = 'django.contrib.sessions.serializers.PickleSerializer'

REST_API_SETTING_1 = 'foo'
REST_API_SETTING_2 = 'bar'
REST_API_SECURITY = 'SECURITY'
REST_API_REQUIRED_SETTINGS = ['REST_API_SETTING_1']
REST_API_ADDITIONAL_SETTINGS = ['REST_API_SETTING_2']
