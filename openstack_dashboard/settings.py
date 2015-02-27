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

import logging
import os
import sys
import warnings

from django.utils.translation import ugettext_lazy as _
import xstatic.main
import xstatic.pkg.angular
import xstatic.pkg.angular_cookies
import xstatic.pkg.angular_mock
import xstatic.pkg.bootstrap_datepicker
import xstatic.pkg.bootstrap_scss
import xstatic.pkg.d3
import xstatic.pkg.font_awesome
import xstatic.pkg.hogan
import xstatic.pkg.jasmine
import xstatic.pkg.jquery
import xstatic.pkg.jquery_migrate
import xstatic.pkg.jquery_quicksearch
import xstatic.pkg.jquery_tablesorter
import xstatic.pkg.jquery_ui
import xstatic.pkg.jsencrypt
import xstatic.pkg.qunit
import xstatic.pkg.rickshaw
import xstatic.pkg.spin

from openstack_dashboard import exceptions

warnings.formatwarning = lambda message, category, *args, **kwargs: \
    '%s: %s' % (category.__name__, message)

ROOT_PATH = os.path.dirname(os.path.abspath(__file__))
BIN_DIR = os.path.abspath(os.path.join(ROOT_PATH, '..', 'bin'))

if ROOT_PATH not in sys.path:
    sys.path.append(ROOT_PATH)

DEBUG = False
TEMPLATE_DEBUG = DEBUG

SITE_BRANDING = 'OpenStack Dashboard'

LOGIN_URL = '/auth/login/'
LOGOUT_URL = '/auth/logout/'
# LOGIN_REDIRECT_URL can be used as an alternative for
# HORIZON_CONFIG.user_home, if user_home is not set.
# Do not set it to '/home/', as this will cause circular redirect loop
LOGIN_REDIRECT_URL = '/'

MEDIA_ROOT = os.path.abspath(os.path.join(ROOT_PATH, '..', 'media'))
MEDIA_URL = '/media/'
STATIC_ROOT = os.path.abspath(os.path.join(ROOT_PATH, '..', 'static'))
STATIC_URL = '/static/'

ROOT_URLCONF = 'openstack_dashboard.urls'

HORIZON_CONFIG = {
    'user_home': 'openstack_dashboard.views.get_user_home',
    'ajax_queue_limit': 10,
    'auto_fade_alerts': {
        'delay': 3000,
        'fade_duration': 1500,
        'types': ['alert-success', 'alert-info']
    },
    'help_url': "http://docs.openstack.org",
    'exceptions': {'recoverable': exceptions.RECOVERABLE,
                   'not_found': exceptions.NOT_FOUND,
                   'unauthorized': exceptions.UNAUTHORIZED},
    'angular_modules': [],
    'js_files': [],
}

# Set to True to allow users to upload images to glance via Horizon server.
# When enabled, a file form field will appear on the create image form.
# See documentation for deployment considerations.
HORIZON_IMAGES_ALLOW_UPLOAD = True

# The OPENSTACK_IMAGE_BACKEND settings can be used to customize features
# in the OpenStack Dashboard related to the Image service, such as the list
# of supported image formats.
OPENSTACK_IMAGE_BACKEND = {
    'image_formats': [
        ('', _('Select format')),
        ('aki', _('AKI - Amazon Kernel Image')),
        ('ami', _('AMI - Amazon Machine Image')),
        ('ari', _('ARI - Amazon Ramdisk Image')),
        ('iso', _('ISO - Optical Disk Image')),
        ('qcow2', _('QCOW2 - QEMU Emulator')),
        ('raw', _('Raw')),
        ('vdi', _('VDI')),
        ('vhd', _('VHD')),
        ('vmdk', _('VMDK'))
    ]
}

MIDDLEWARE_CLASSES = (
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'openstack_dashboard.fiware_middleware.middleware.UserInfoMiddleware',
    'openstack_dashboard.fiware_middleware.middleware.OrganizationInfoMiddleware',
    'openstack_dashboard.fiware_middleware.middleware.SwitchMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'horizon.middleware.HorizonMiddleware',
    'django.middleware.doc.XViewMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
)

TEMPLATE_CONTEXT_PROCESSORS = (
    'django.core.context_processors.debug',
    'django.core.context_processors.i18n',
    'django.core.context_processors.request',
    'django.core.context_processors.media',
    'django.core.context_processors.static',
    'django.contrib.messages.context_processors.messages',
    'horizon.context_processors.horizon',
    'openstack_dashboard.context_processors.openstack',
)

TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.Loader',
    'django.template.loaders.app_directories.Loader',
    'horizon.loaders.TemplateLoader'
)

TEMPLATE_DIRS = (
    os.path.join(ROOT_PATH, 'templates'),
)

STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
    'compressor.finders.CompressorFinder',
)

STATICFILES_DIRS = [
    ('horizon/lib/angular',
        xstatic.main.XStatic(xstatic.pkg.angular).base_dir),
    ('horizon/lib/angular',
        xstatic.main.XStatic(xstatic.pkg.angular_cookies).base_dir),
    ('horizon/lib/angular',
        xstatic.main.XStatic(xstatic.pkg.angular_mock).base_dir),
    ('horizon/lib/bootstrap_datepicker',
        xstatic.main.XStatic(xstatic.pkg.bootstrap_datepicker).base_dir),
    ('bootstrap',
        xstatic.main.XStatic(xstatic.pkg.bootstrap_scss).base_dir),
    ('horizon/lib',
        xstatic.main.XStatic(xstatic.pkg.d3).base_dir),
    ('horizon/lib',
        xstatic.main.XStatic(xstatic.pkg.hogan).base_dir),
    ('horizon/lib/font-awesome',
        xstatic.main.XStatic(xstatic.pkg.font_awesome).base_dir),
    ('horizon/lib/jasmine-1.3.1',
        xstatic.main.XStatic(xstatic.pkg.jasmine).base_dir),
    ('horizon/lib/jquery',
        xstatic.main.XStatic(xstatic.pkg.jquery).base_dir),
    ('horizon/lib/jquery',
        xstatic.main.XStatic(xstatic.pkg.jquery_migrate).base_dir),
    ('horizon/lib/jquery',
        xstatic.main.XStatic(xstatic.pkg.jquery_quicksearch).base_dir),
    ('horizon/lib/jquery',
        xstatic.main.XStatic(xstatic.pkg.jquery_tablesorter).base_dir),
    ('horizon/lib/jsencrypt',
        xstatic.main.XStatic(xstatic.pkg.jsencrypt).base_dir),
    ('horizon/lib/qunit',
        xstatic.main.XStatic(xstatic.pkg.qunit).base_dir),
    ('horizon/lib',
        xstatic.main.XStatic(xstatic.pkg.rickshaw).base_dir),
    ('horizon/lib',
        xstatic.main.XStatic(xstatic.pkg.spin).base_dir),
]


if xstatic.main.XStatic(xstatic.pkg.jquery_ui).version.startswith('1.10.'):
    # The 1.10.x versions already contain the 'ui' directory.
    STATICFILES_DIRS.append(
        ('horizon/lib/jquery-ui',
         xstatic.main.XStatic(xstatic.pkg.jquery_ui).base_dir))
else:
    # Newer versions dropped the directory, add it to keep the path the same.
    STATICFILES_DIRS.append(
        ('horizon/lib/jquery-ui/ui',
         xstatic.main.XStatic(xstatic.pkg.jquery_ui).base_dir))

COMPRESS_PRECOMPILERS = (
    ('text/scss', 'django_pyscss.compressor.DjangoScssFilter'),
)

COMPRESS_CSS_FILTERS = (
    'compressor.filters.css_default.CssAbsoluteFilter',
)

COMPRESS_ENABLED = True
COMPRESS_OUTPUT_DIR = 'dashboard'
COMPRESS_CSS_HASHING_METHOD = 'hash'
COMPRESS_PARSER = 'compressor.parser.HtmlParser'

INSTALLED_APPS = [
    'openstack_dashboard',
    'django.contrib.contenttypes',
    'django.contrib.auth',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.humanize',
    'django_pyscss',
    'openstack_dashboard.django_pyscss_fix',
    'compressor',
    'horizon',
    'openstack_auth',
    'captcha',
    'django_summernote', 
]
TEST_RUNNER = 'django_nose.NoseTestSuiteRunner'
AUTHENTICATION_BACKENDS = ('openstack_auth.backend.KeystoneBackend',)
MESSAGE_STORAGE = 'django.contrib.messages.storage.fallback.FallbackStorage'

SESSION_ENGINE = 'django.contrib.sessions.backends.signed_cookies'
SESSION_COOKIE_HTTPONLY = True
SESSION_EXPIRE_AT_BROWSER_CLOSE = True
SESSION_COOKIE_SECURE = False
SESSION_TIMEOUT = 1800
# A token can be near the end af validity when a page starts loading, and
# invalid during the rendering which can cause errors when a page load.
# TOKEN_TIMEOUT_MARGIN defines a time in seconds we retrieve from token
# validity to avoid this issue. You can adjust this time depending on the
# performance of the infrastructure.
TOKEN_TIMEOUT_MARGIN = 10

# When using cookie-based sessions, log error when the session cookie exceeds
# the following size (common browsers drop cookies above a certain size):
SESSION_COOKIE_MAX_SIZE = 4093

# when doing upgrades, it may be wise to stick to PickleSerializer
# NOTE(berendt): Check during the K-cycle if this variable can be removed.
#                https://bugs.launchpad.net/horizon/+bug/1349463
SESSION_SERIALIZER = 'django.contrib.sessions.serializers.PickleSerializer'

LANGUAGES = (
    ('de', 'German'),
    ('en', 'English'),
    ('en-au', 'Australian English'),
    ('en-gb', 'British English'),
    ('es', 'Spanish'),
    ('fr', 'French'),
    ('hi', 'Hindi'),
    ('ja', 'Japanese'),
    ('ko', 'Korean (Korea)'),
    ('pl', 'Polish'),
    ('pt-br', 'Portuguese (Brazil)'),
    ('zh-cn', 'Simplified Chinese'),
    ('zh-tw', 'Chinese (Taiwan)'),
)
LANGUAGE_CODE = 'en'
LANGUAGE_COOKIE_NAME = 'horizon_language'
USE_I18N = True
USE_L10N = True
USE_TZ = True

OPENSTACK_KEYSTONE_DEFAULT_ROLE = '_member_'

DEFAULT_EXCEPTION_REPORTER_FILTER = 'horizon.exceptions.HorizonReporterFilter'

POLICY_FILES_PATH = os.path.join(ROOT_PATH, "conf")
# Map of local copy of service policy files
POLICY_FILES = {
    'identity': 'keystone_policy.json',
    'compute': 'nova_policy.json',
    'volume': 'cinder_policy.json',
    'image': 'glance_policy.json',
    'orchestration': 'heat_policy.json',
    'network': 'neutron_policy.json',
}

SECRET_KEY = None
LOCAL_PATH = None

SECURITY_GROUP_RULES = {
    'all_tcp': {
        'name': _('All TCP'),
        'ip_protocol': 'tcp',
        'from_port': '1',
        'to_port': '65535',
    },
    'all_udp': {
        'name': _('All UDP'),
        'ip_protocol': 'udp',
        'from_port': '1',
        'to_port': '65535',
    },
    'all_icmp': {
        'name': _('All ICMP'),
        'ip_protocol': 'icmp',
        'from_port': '-1',
        'to_port': '-1',
    },
}

try:
    from local.local_settings import *  # noqa
except ImportError:
    logging.warning("No local_settings file found.")

# Load the pluggable dashboard settings
import openstack_dashboard.enabled
import openstack_dashboard.local.enabled
from openstack_dashboard.utils import settings

INSTALLED_APPS = list(INSTALLED_APPS)  # Make sure it's mutable
settings.update_dashboards([
    openstack_dashboard.enabled,
    openstack_dashboard.local.enabled,
], HORIZON_CONFIG, INSTALLED_APPS)

# Ensure that we always have a SECRET_KEY set, even when no local_settings.py
# file is present. See local_settings.py.example for full documentation on the
# horizon.utils.secret_key module and its use.
if not SECRET_KEY:
    if not LOCAL_PATH:
        LOCAL_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                  'local')

    from horizon.utils import secret_key
    SECRET_KEY = secret_key.generate_or_read_from_file(os.path.join(LOCAL_PATH,
                                                       '.secret_key_store'))

from openstack_dashboard import policy
#POLICY_CHECK_FUNCTION = policy.check

# Add HORIZON_CONFIG to the context information for offline compression
COMPRESS_OFFLINE_CONTEXT = {
    'STATIC_URL': STATIC_URL,
    'HORIZON_CONFIG': HORIZON_CONFIG
}

if DEBUG:
    logging.basicConfig(level=logging.DEBUG)

# during django reloads and an active user is logged in, the monkey
# patch below will not otherwise be applied in time - resulting in developers
# appearing to be logged out.  In typical production deployments this section
# below may be omitted, though it should not be harmful
from openstack_auth import utils as auth_utils
auth_utils.patch_middleware_get_user()
