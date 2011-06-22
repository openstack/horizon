import os

ROOT_PATH = os.path.dirname(os.path.abspath(__file__))
DEBUG = True
TESTSERVER = 'http://testserver'
DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': '/tmp/django-openstack.db',
            },
        }
INSTALLED_APPS = ['django.contrib.auth',
                  'django.contrib.contenttypes',
                  'django.contrib.sessions',
                  'django.contrib.sites',
                  'django_openstack',
                  'django_openstack.tests',
                  'django_openstack.templatetags',
                  'mailer',
                  ]
ROOT_URLCONF = 'django_openstack.tests.testurls'
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

TEST_RUNNER = 'django_nose.NoseTestSuiteRunner'
NOSE_ARGS = ['--nocapture',
            ]

# django-mailer uses a different config attribute
# even though it just wraps django.core.mail
MAILER_EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'
EMAIL_BACKEND = MAILER_EMAIL_BACKEND

