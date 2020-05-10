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

import glob
import logging
import os
import sys
import warnings

from django.utils.translation import ugettext_lazy as _

import openstack_auth

import horizon
from horizon.utils.escape import monkeypatch_escape

import openstack_dashboard
from openstack_dashboard import enabled
from openstack_dashboard import exceptions
from openstack_dashboard.local import enabled as local_enabled
from openstack_dashboard import theme_settings
from openstack_dashboard.utils import config
from openstack_dashboard.utils import settings as settings_utils

monkeypatch_escape()

# Load default values
# pylint: disable=wrong-import-position
from openstack_dashboard.defaults import *  # noqa: E402,F403,H303

_LOG = logging.getLogger(__name__)

warnings.formatwarning = lambda message, category, *args, **kwargs: \
    '%s: %s' % (category.__name__, message)

ROOT_PATH = os.path.dirname(os.path.abspath(__file__))

if ROOT_PATH not in sys.path:
    sys.path.append(ROOT_PATH)

DEBUG = False

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
    'help_url': "https://docs.openstack.org/",
    'exceptions': {'recoverable': exceptions.RECOVERABLE,
                   'not_found': exceptions.NOT_FOUND,
                   'unauthorized': exceptions.UNAUTHORIZED},
    'modal_backdrop': 'static',
    'angular_modules': [],
    'js_files': [],
    'js_spec_files': [],
    'external_templates': [],
    'plugins': [],
    'integration_tests_support': INTEGRATION_TESTS_SUPPORT
}

MIDDLEWARE = (
    'openstack_auth.middleware.OpenstackAuthMonkeyPatchMiddleware',
    'debreach.middleware.RandomCommentMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'horizon.middleware.OperationLogMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'horizon.middleware.HorizonMiddleware',
    'horizon.themes.ThemeMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'openstack_dashboard.contrib.developer.profiler.middleware.'
    'ProfilerClientMiddleware',
    'openstack_dashboard.contrib.developer.profiler.middleware.'
    'ProfilerMiddleware',
)

CACHED_TEMPLATE_LOADERS = [
    'django.template.loaders.filesystem.Loader',
    'django.template.loaders.app_directories.Loader',
    'horizon.loaders.TemplateLoader'
]

ADD_TEMPLATE_LOADERS = []
ADD_TEMPLATE_DIRS = []

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(ROOT_PATH, 'templates')],
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.i18n',
                'django.template.context_processors.request',
                'django.template.context_processors.media',
                'django.template.context_processors.static',
                'django.contrib.messages.context_processors.messages',
                'horizon.context_processors.horizon',
                'openstack_dashboard.context_processors.openstack',
            ],
            'loaders': [
                'horizon.themes.ThemeTemplateLoader'
            ],
        },
    },
]

STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'horizon.contrib.staticfiles.finders.HorizonStaticFinder',
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
    'debreach',
    'openstack_dashboard.django_pyscss_fix',
    'compressor',
    'horizon',
    'openstack_auth',
]

AUTHENTICATION_BACKENDS = ('openstack_auth.backend.KeystoneBackend',)
AUTH_USER_MODEL = 'openstack_auth.User'
MESSAGE_STORAGE = 'django.contrib.messages.storage.fallback.FallbackStorage'

SESSION_ENGINE = 'django.contrib.sessions.backends.cache'
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.memcached.MemcachedCache',
        'LOCATION': '127.0.0.1:11211',
    },
}

SESSION_COOKIE_HTTPONLY = True
SESSION_EXPIRE_AT_BROWSER_CLOSE = True
SESSION_COOKIE_SECURE = False

# when doing upgrades, it may be wise to stick to PickleSerializer
# NOTE(berendt): Check during the K-cycle if this variable can be removed.
#                https://bugs.launchpad.net/horizon/+bug/1349463
SESSION_SERIALIZER = 'django.contrib.sessions.serializers.PickleSerializer'

CSRF_FAILURE_VIEW = 'openstack_dashboard.views.csrf_failure'

LANGUAGES = (
    ('cs', 'Czech'),
    ('de', 'German'),
    ('en', 'English'),
    ('en-au', 'Australian English'),
    ('en-gb', 'British English'),
    ('eo', 'Esperanto'),
    ('es', 'Spanish'),
    ('fr', 'French'),
    ('id', 'Indonesian'),
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

DEFAULT_EXCEPTION_REPORTER_FILTER = 'horizon.exceptions.HorizonReporterFilter'

SECRET_KEY = None
LOCAL_PATH = None

ADD_INSTALLED_APPS = []

CSRF_COOKIE_AGE = None

COMPRESS_OFFLINE_CONTEXT = 'horizon.themes.offline_context'

# Notice all customizable configurations should be above this line
XSTATIC_MODULES = settings_utils.BASE_XSTATIC_MODULES

if not LOCAL_PATH:
    LOCAL_PATH = os.path.join(ROOT_PATH, 'local')
LOCAL_SETTINGS_DIR_PATH = os.path.join(LOCAL_PATH, "local_settings.d")

_files = glob.glob(os.path.join(LOCAL_PATH, 'local_settings.conf'))
_files.extend(
    sorted(glob.glob(os.path.join(LOCAL_SETTINGS_DIR_PATH, '*.conf'))))
_config = config.load_config(_files, ROOT_PATH, LOCAL_PATH)

# Apply the general configuration.
config.apply_config(_config, globals())

try:
    from local.local_settings import *  # noqa: F403,H303
except ImportError:
    _LOG.warning("No local_settings file found.")

# configure templates
if not TEMPLATES[0]['DIRS']:
    TEMPLATES[0]['DIRS'] = [os.path.join(ROOT_PATH, 'templates')]

TEMPLATES[0]['DIRS'] += ADD_TEMPLATE_DIRS

# configure template debugging
TEMPLATES[0]['OPTIONS']['debug'] = DEBUG

# Template loaders
if DEBUG:
    TEMPLATES[0]['OPTIONS']['loaders'].extend(
        CACHED_TEMPLATE_LOADERS + ADD_TEMPLATE_LOADERS
    )
else:
    TEMPLATES[0]['OPTIONS']['loaders'].extend(
        [('django.template.loaders.cached.Loader', CACHED_TEMPLATE_LOADERS)] +
        ADD_TEMPLATE_LOADERS
    )

# allow to drop settings snippets into a local_settings_dir
LOCAL_SETTINGS_DIR_PATH = os.path.join(ROOT_PATH, "local", "local_settings.d")
if os.path.exists(LOCAL_SETTINGS_DIR_PATH):
    for (dirpath, dirnames, filenames) in os.walk(LOCAL_SETTINGS_DIR_PATH):
        for filename in sorted(filenames):
            if filename.endswith(".py"):
                try:
                    with open(os.path.join(dirpath, filename)) as f:
                        # pylint: disable=exec-used
                        exec(f.read())
                except Exception as e:
                    _LOG.exception(
                        "Can not exec settings snippet %s", filename)

# The purpose of OPENSTACK_IMAGE_FORMATS is to provide a simple object
# that does not contain the lazy-loaded translations, so the list can
# be sent as JSON to the client-side (Angular).
# TODO(amotoki): Do we really need this here? Can't we calculate this
# in openstack_dashboard.api.rest.config?
OPENSTACK_IMAGE_FORMATS = [fmt for (fmt, name)
                           in OPENSTACK_IMAGE_BACKEND['image_formats']]

if USER_MENU_LINKS is None:
    USER_MENU_LINKS = []
    if SHOW_OPENRC_FILE:
        USER_MENU_LINKS.append({
            'name': _('OpenStack RC File'),
            'icon_classes': ['fa-download', ],
            'url': 'horizon:project:api_access:openrc',
        })

if not WEBROOT.endswith('/'):
    WEBROOT += '/'
if LOGIN_URL is None:
    LOGIN_URL = WEBROOT + 'auth/login/'
if LOGOUT_URL is None:
    LOGOUT_URL = WEBROOT + 'auth/logout/'
if LOGIN_ERROR is None:
    LOGIN_ERROR = WEBROOT + 'auth/error/'
if LOGIN_REDIRECT_URL is None:
    LOGIN_REDIRECT_URL = WEBROOT

if MEDIA_ROOT is None:
    MEDIA_ROOT = os.path.abspath(os.path.join(ROOT_PATH, '..', 'media'))

if MEDIA_URL is None:
    MEDIA_URL = WEBROOT + 'media/'

if STATIC_ROOT is None:
    STATIC_ROOT = os.path.abspath(os.path.join(ROOT_PATH, '..', 'static'))

if STATIC_URL is None:
    STATIC_URL = WEBROOT + 'static/'

AVAILABLE_THEMES, SELECTABLE_THEMES, DEFAULT_THEME = (
    theme_settings.get_available_themes(
        AVAILABLE_THEMES,
        DEFAULT_THEME,
        SELECTABLE_THEMES
    )
)

# Discover all the directories that contain static files
STATICFILES_DIRS = theme_settings.get_theme_static_dirs(
    AVAILABLE_THEMES, THEME_COLLECTION_DIR, ROOT_PATH)

# Ensure that we always have a SECRET_KEY set, even when no local_settings.py
# file is present. See local_settings.py.example for full documentation on the
# horizon.utils.secret_key module and its use.
if not SECRET_KEY:
    if not LOCAL_PATH:
        LOCAL_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                  'local')

    # pylint: disable=ungrouped-imports
    from horizon.utils import secret_key
    SECRET_KEY = secret_key.generate_or_read_from_file(os.path.join(LOCAL_PATH,
                                                       '.secret_key_store'))

# populate HORIZON_CONFIG with auto-discovered JavaScript sources, mock files,
# specs files and external templates.
settings_utils.find_static_files(HORIZON_CONFIG, AVAILABLE_THEMES,
                                 THEME_COLLECTION_DIR, ROOT_PATH)

INSTALLED_APPS = list(INSTALLED_APPS)  # Make sure it's mutable
settings_utils.update_dashboards(
    [
        enabled,
        local_enabled,
    ],
    HORIZON_CONFIG,
    INSTALLED_APPS,
)
INSTALLED_APPS[0:0] = ADD_INSTALLED_APPS

# Include xstatic_modules specified in plugin
XSTATIC_MODULES += HORIZON_CONFIG['xstatic_modules']

# Discover all the xstatic module entry points to embed in our HTML
STATICFILES_DIRS += settings_utils.get_xstatic_dirs(
    XSTATIC_MODULES, HORIZON_CONFIG)

# This base context objects gets added to the offline context generator
# for each theme configured.
HORIZON_COMPRESS_OFFLINE_CONTEXT_BASE = {
    'WEBROOT': WEBROOT,
    'STATIC_URL': STATIC_URL,
    'HORIZON_CONFIG': HORIZON_CONFIG,
    'NG_TEMPLATE_CACHE_AGE': NG_TEMPLATE_CACHE_AGE if not DEBUG else 0,
}

if DEBUG:
    logging.basicConfig(level=logging.DEBUG)

# NOTE(e0ne): Set absolute paths for directories with localization.
# Django doesn't work well for Taiwanese locale with relative paths
# wich are used by default and I can't figure out at the moment why it
# works in this way. We don't use default Django templates, so it should
# be safe to have such defaults
LOCALE_PATHS = [
    os.path.join(os.path.dirname(os.path.abspath(m.__file__)), 'locale')
    for m in (horizon, openstack_dashboard, openstack_auth)
]
# Here comes the Django settings deprecation section. Being at the very end
# of settings.py allows it to catch the settings defined in local_settings.py
# or inside one of local_settings.d/ snippets.
