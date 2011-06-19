import os

ROOT_PATH = os.path.dirname(os.path.abspath(__file__))
DEBUG = True
TESTSERVER = 'http://testserver'
DATABASE_ENGINE = 'sqlite3'
DATABASE_NAME = '/tmp/django-openstack.db'
INSTALLED_APPS = ['django.contrib.auth',
                  'django.contrib.contenttypes',
                  'django.contrib.sessions',
                  'django.contrib.sites',
                  'django_openstack',
                  'django_openstack.tests',
                  'django_openstack.templatetags',
                  'django_openstack.nova']
ROOT_URLCONF = 'django_openstack.testurls'
TEMPLATE_DIRS = (
    os.path.join(ROOT_PATH, 'tests', 'templates')
)
SITE_ID = 1
SITE_BRANDING = 'OpenStack'
SITE_NAME = 'openstack'
ENABLE_VNC = True
NOVA_DEFAULT_ENDPOINT = None
NOVA_DEFAULT_REGION = 'test'
NOVA_ACCESS_KEY = 'test'
NOVA_SECRET_KEY = 'test'

CREDENTIAL_AUTHORIZATION_DAYS = 2
CREDENTIAL_DOWNLOAD_URL = TESTSERVER + '/credentials/'
