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
import tempfile

import six

from django.utils.translation import pgettext_lazy
from horizon.test.settings import *  # noqa: F403,H303
from horizon.utils import secret_key
from openstack_dashboard import exceptions

from horizon.utils.escape import monkeypatch_escape

# this is used to protect from client XSS attacks, but it's worth
# enabling in our test setup to find any issues it might cause
monkeypatch_escape()

from openstack_dashboard.utils import settings as settings_utils

TEST_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_PATH = os.path.abspath(os.path.join(TEST_DIR, ".."))
MEDIA_ROOT = os.path.abspath(os.path.join(ROOT_PATH, '..', 'media'))
MEDIA_URL = '/media/'
STATIC_ROOT = os.path.abspath(os.path.join(ROOT_PATH, '..', 'static'))
STATIC_URL = '/static/'
WEBROOT = '/'

SECRET_KEY = secret_key.generate_or_read_from_file(
    os.path.join(tempfile.gettempdir(), '.secret_key_store'))
ROOT_URLCONF = 'openstack_dashboard.test.urls'

TEMPLATES[0]['DIRS'] = [
    os.path.join(TEST_DIR, 'templates')
]

TEMPLATES[0]['OPTIONS']['context_processors'].append(
    'openstack_dashboard.context_processors.openstack'
)

CUSTOM_THEME_PATH = 'themes/default'

# 'key', 'label', 'path'
AVAILABLE_THEMES = [
    (
        'default',
        pgettext_lazy('Default style theme', 'Default'),
        'themes/default'
    ), (
        'material',
        pgettext_lazy("Google's Material Design style theme", "Material"),
        'themes/material'
    ),
]

SELECTABLE_THEMES = [
    (
        'default',
        pgettext_lazy('Default style theme', 'Default'),
        'themes/default'
    ),
]

# Theme Static Directory
THEME_COLLECTION_DIR = 'themes'

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

ANGULAR_FEATURES = {
    'images_panel': False,  # Use the legacy panel so unit tests are still run
    'flavors_panel': False,
    'roles_panel': False,
}

STATICFILES_DIRS = settings_utils.get_xstatic_dirs(
    settings_utils.BASE_XSTATIC_MODULES, HORIZON_CONFIG
)

# Load the pluggable dashboard settings
import openstack_dashboard.enabled

INSTALLED_APPS = list(INSTALLED_APPS)  # Make sure it's mutable
settings_utils.update_dashboards(
    [
        openstack_dashboard.enabled,
    ],
    HORIZON_CONFIG,
    INSTALLED_APPS,
)

OPENSTACK_PROFILER = {'enabled': False}

settings_utils.find_static_files(HORIZON_CONFIG, AVAILABLE_THEMES,
                                 THEME_COLLECTION_DIR, ROOT_PATH)

# Set to 'legacy' or 'direct' to allow users to upload images to glance via
# Horizon server. When enabled, a file form field will appear on the create
# image form. If set to 'off', there will be no file form field on the create
# image form. See documentation for deployment considerations.
HORIZON_IMAGES_UPLOAD_MODE = 'legacy'

AVAILABLE_REGIONS = [
    ('http://localhost:5000/v2.0', 'local'),
    ('http://remote:5000/v2.0', 'remote'),
]

OPENSTACK_API_VERSIONS = {
    "identity": 3,
    "image": 2
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
    'enable_distributed_router': False,
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
        ('ploop', 'PLOOP - Virtuozzo/Parallels Loopback Disk'),
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
# TODO(amotoki): Need to investigate why --with-html-output
# is unavailable in python3.
# NOTE(amotoki): Most horizon plugins import this module in their test
# settings and they do not necessarily have nosehtmloutput in test-reqs.
# Assuming nosehtmloutput potentially breaks plugins tests,
# we check the availability of htmloutput module (from nosehtmloutput).
try:
    import htmloutput  # noqa: F401
    has_html_output = True
except ImportError:
    has_html_output = False
if six.PY2 and has_html_output:
    NOSE_ARGS += ['--with-html-output',
                  '--html-out-file=ut_openstack_dashboard_nose_results.html']

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

ALLOWED_PRIVATE_SUBNET_CIDR = {'ipv4': [], 'ipv6': []}


# --------------------
# Test-only settings
# --------------------
# TEST_GLOBAL_MOCKS_ON_PANELS: defines what and how methods should be
# mocked globally for unit tests and Selenium tests.
# 'method' is required. 'return_value' and 'side_effect'
# are optional and passed to mock.patch().
TEST_GLOBAL_MOCKS_ON_PANELS = {
    'aggregates': {
        'method': ('openstack_dashboard.dashboards.admin'
                   '.aggregates.panel.Aggregates.can_access'),
        'return_value': True,
    },
    'domains': {
        'method': ('openstack_dashboard.dashboards.identity'
                   '.domains.panel.Domains.can_access'),
        'return_value': True,
    },
    'trunk': {
        'method': ('openstack_dashboard.dashboards.project'
                   '.trunks.panel.Trunks.can_access'),
        'return_value': True,
    },
    'qos': {
        'method': ('openstack_dashboard.dashboards.project'
                   '.network_qos.panel.NetworkQoS.can_access'),
        'return_value': True,
    },
}
