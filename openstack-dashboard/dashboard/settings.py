import boto
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

LOGIN_URL = '/accounts/login'
LOGIN_REDIRECT_URL = '/'

MEDIA_ROOT = os.path.join(ROOT_PATH, '..', 'media')
MEDIA_URL = '/media/'
ADMIN_MEDIA_PREFIX = '/media/admin/'

CREDENTIAL_AUTHORIZATION_DAYS = '5'

ROOT_URLCONF = 'dashboard.urls'

MIDDLEWARE_CLASSES = (
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.middleware.doc.XViewMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'dashboard.middleware.DashboardLogUnhandledExceptionsMiddleware',
)

TEMPLATE_CONTEXT_PROCESSORS = (
    'django.core.context_processors.auth',
    'django.core.context_processors.debug',
    'django.core.context_processors.i18n',
    'django.core.context_processors.request',
    'django.core.context_processors.media',
    'django.contrib.messages.context_processors.messages',
)

TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.load_template_source',
    'django.template.loaders.app_directories.load_template_source',
)

TEMPLATE_DIRS = (
    os.path.join(ROOT_PATH, 'templates'),
)

INSTALLED_APPS = (
    'dashboard',
    'django.contrib.auth',
    'django.contrib.admin',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.comments',
    'django.contrib.sites',
    'django.contrib.markup',
    'django.contrib.syndication',
    'django_nose',
    'django_openstack',
    'django_openstack.nova',
    'django_openstack.templatetags',
    'django_nova_syspanel',
    'registration',
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

# NOTE(devcamcar): Prevent boto from retrying and stalling the connection.
if not boto.config.has_section('Boto'):
    boto.config.add_section('Boto')
boto.config.set('Boto', 'num_retries', '0')

try:
    from local.local_settings import *
except Exception, e:
    logging.exception(e)

if DEBUG:
    logging.basicConfig(level=logging.DEBUG)
