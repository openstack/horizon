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

from django.utils.translation import pgettext_lazy
from django.utils.translation import ugettext_lazy as _

from openstack_dashboard import exceptions
from openstack_dashboard.static_settings import find_static_files  # noqa
from openstack_dashboard.static_settings import get_staticfiles_dirs  # noqa
from openstack_dashboard import theme_settings


warnings.formatwarning = lambda message, category, *args, **kwargs: \
    '%s: %s' % (category.__name__, message)

ROOT_PATH = os.path.dirname(os.path.abspath(__file__))
BIN_DIR = os.path.abspath(os.path.join(ROOT_PATH, '..', 'bin'))

if ROOT_PATH not in sys.path:
    sys.path.append(ROOT_PATH)

DEBUG = False
TEMPLATE_DEBUG = DEBUG

SITE_BRANDING = 'OpenStack Dashboard'

WEBROOT = '/'
LOGIN_URL = None
LOGOUT_URL = None
LOGIN_REDIRECT_URL = None
STATIC_ROOT = None
STATIC_URL = None

ROOT_URLCONF = 'openstack_dashboard.urls'

HORIZON_CONFIG = {
    'user_home': 'openstack_dashboard.views.get_user_home',
    'ajax_queue_limit': 10,
    'auto_fade_alerts': {
        'delay': 3000,
        'fade_duration': 1500,
        'types': ['alert-success', 'alert-info']
    },
    'bug_url': None,
    'help_url': "http://docs.openstack.org",
    'exceptions': {'recoverable': exceptions.RECOVERABLE,
                   'not_found': exceptions.NOT_FOUND,
                   'unauthorized': exceptions.UNAUTHORIZED},
    'modal_backdrop': 'static',
    'angular_modules': [],
    'js_files': [],
    'js_spec_files': [],
    'external_templates': [],
    'plugins': []
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
        ('docker', _('Docker')),
        ('iso', _('ISO - Optical Disk Image')),
        ('ova', _('OVA - Open Virtual Appliance')),
        ('qcow2', _('QCOW2 - QEMU Emulator')),
        ('raw', _('Raw')),
        ('vdi', _('VDI - Virtual Disk Image')),
        ('vhd', _('VHD - Virtual Hard Disk')),
        ('vmdk', _('VMDK - Virtual Machine Disk')),
    ]
}

MIDDLEWARE_CLASSES = (
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.contrib.auth.middleware.SessionAuthenticationMiddleware',
    'horizon.middleware.HorizonMiddleware',
    'horizon.themes.ThemeMiddleware',
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

TEMPLATE_DIRS = (
    os.path.join(ROOT_PATH, 'templates'),
)

STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
    'compressor.finders.CompressorFinder',
)

COMPRESS_PRECOMPILERS = (
    ('text/scss', 'horizon.utils.scss_filter.HorizonScssFilter'),
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
]

TEST_RUNNER = 'django_nose.NoseTestSuiteRunner'
AUTHENTICATION_BACKENDS = ('openstack_auth.backend.KeystoneBackend',)
AUTHENTICATION_URLS = ['openstack_auth.urls']
AUTH_USER_MODEL = 'openstack_auth.User'
MESSAGE_STORAGE = 'django.contrib.messages.storage.fallback.FallbackStorage'

SESSION_ENGINE = 'django.contrib.sessions.backends.signed_cookies'
SESSION_COOKIE_HTTPONLY = True
SESSION_EXPIRE_AT_BROWSER_CLOSE = True
SESSION_COOKIE_SECURE = False

# SESSION_TIMEOUT is a method to supersede the token timeout with a shorter
# horizon session timeout (in seconds).  So if your token expires in 60
# minutes, a value of 1800 will log users out after 30 minutes
SESSION_TIMEOUT = 3600

# When using cookie-based sessions, log error when the session cookie exceeds
# the following size (common browsers drop cookies above a certain size):
SESSION_COOKIE_MAX_SIZE = 4093

# when doing upgrades, it may be wise to stick to PickleSerializer
# NOTE(berendt): Check during the K-cycle if this variable can be removed.
#                https://bugs.launchpad.net/horizon/+bug/1349463
SESSION_SERIALIZER = 'django.contrib.sessions.serializers.PickleSerializer'

LANGUAGES = (
    ('cs', 'Czech'),
    ('de', 'German'),
    ('en', 'English'),
    ('en-au', 'Australian English'),
    ('en-gb', 'British English'),
    ('es', 'Spanish'),
    ('fr', 'French'),
    ('it', 'Italian'),
    ('ja', 'Japanese'),
    ('ko', 'Korean (Korea)'),
    ('pl', 'Polish'),
    ('pt-br', 'Portuguese (Brazil)'),
    ('ru', 'Russian'),
    ('tr', 'Turkish'),
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
    'telemetry': 'ceilometer_policy.json',
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

ADD_INSTALLED_APPS = []

# Deprecated Theme Settings
CUSTOM_THEME_PATH = None
DEFAULT_THEME_PATH = None

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

# The default theme if no cookie is present
DEFAULT_THEME = 'default'

# Theme Static Directory
THEME_COLLECTION_DIR = 'themes'

# Theme Cookie Name
THEME_COOKIE_NAME = 'theme'

try:
    from local.local_settings import *  # noqa
except ImportError:
    logging.warning("No local_settings file found.")

_LOADERS = ('django.template.loaders.filesystem.Loader',
            'django.template.loaders.app_directories.Loader',
            'horizon.loaders.TemplateLoader',)

if DEBUG:
    TEMPLATE_LOADERS = ('horizon.themes.ThemeTemplateLoader',) + _LOADERS
else:
    TEMPLATE_LOADERS = ('horizon.themes.ThemeTemplateLoader',
                        ('django.template.loaders.cached.Loader', _LOADERS),)

# allow to drop settings snippets into a local_settings_dir
LOCAL_SETTINGS_DIR_PATH = os.path.join(ROOT_PATH, "local", "local_settings.d")
if os.path.exists(LOCAL_SETTINGS_DIR_PATH):
    for (dirpath, dirnames, filenames) in os.walk(LOCAL_SETTINGS_DIR_PATH):
        for filename in sorted(filenames):
            if filename.endswith(".py"):
                try:
                    execfile(os.path.join(dirpath, filename))
                except Exception as e:
                    logging.exception(
                        "Can not exec settings snippet %s" % filename)


if not WEBROOT.endswith('/'):
    WEBROOT += '/'
if LOGIN_URL is None:
    LOGIN_URL = WEBROOT + 'auth/login/'
if LOGOUT_URL is None:
    LOGOUT_URL = WEBROOT + 'auth/logout/'
if LOGIN_REDIRECT_URL is None:
    LOGIN_REDIRECT_URL = WEBROOT

MEDIA_ROOT = os.path.abspath(os.path.join(ROOT_PATH, '..', 'media'))
MEDIA_URL = WEBROOT + 'media/'

if STATIC_ROOT is None:
    STATIC_ROOT = os.path.abspath(os.path.join(ROOT_PATH, '..', 'static'))

if STATIC_URL is None:
    STATIC_URL = WEBROOT + 'static/'

AVAILABLE_THEMES, DEFAULT_THEME = theme_settings.get_available_themes(
    AVAILABLE_THEMES,
    CUSTOM_THEME_PATH,
    DEFAULT_THEME_PATH,
    DEFAULT_THEME
)

STATICFILES_DIRS = get_staticfiles_dirs(STATIC_URL) + \
    theme_settings.get_theme_static_dirs(
        AVAILABLE_THEMES,
        THEME_COLLECTION_DIR,
        ROOT_PATH)

if CUSTOM_THEME_PATH is not None:
    logging.warning("CUSTOM_THEME_PATH has been deprecated.  Please convert "
                    "your settings to make use of AVAILABLE_THEMES.")

if DEFAULT_THEME_PATH is not None:
    logging.warning("DEFAULT_THEME_PATH has been deprecated.  Please convert "
                    "your settings to make use of AVAILABLE_THEMES.")

# populate HORIZON_CONFIG with auto-discovered JavaScript sources, mock files,
# specs files and external templates.
find_static_files(HORIZON_CONFIG)

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
INSTALLED_APPS[0:0] = ADD_INSTALLED_APPS


def check(actions, request, target=None):
    # Note(Itxaka): This is to prevent circular dependencies and apps not ready
    # If you do django imports in your settings, you are gonna have a bad time
    from openstack_auth import policy
    return policy.check(actions, request, target=None)

POLICY_CHECK_FUNCTION = check

# This base context objects gets added to the offline context generator
# for each theme configured.
HORIZON_COMPRESS_OFFLINE_CONTEXT_BASE = {
    'WEBROOT': WEBROOT,
    'STATIC_URL': STATIC_URL,
    'HORIZON_CONFIG': HORIZON_CONFIG
}

COMPRESS_OFFLINE_CONTEXT = 'horizon.themes.offline_context'

if DEBUG:
    logging.basicConfig(level=logging.DEBUG)

CSRF_COOKIE_AGE = None
