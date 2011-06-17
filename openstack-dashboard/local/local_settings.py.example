import os

DEBUG = True
TEMPLATE_DEBUG = DEBUG
PROD = False
USE_SSL = False

LOCAL_PATH = os.path.dirname(os.path.abspath(__file__))
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(LOCAL_PATH, 'dashboard_openstack.sqlite3'),
    },
}

CACHE_BACKEND = 'dummy://'

# Configure these for your outgoing email host
# EMAIL_HOST = 'smtp.my-company.com'
# EMAIL_PORT = 25
# EMAIL_HOST_USER = 'djangomail'
# EMAIL_HOST_PASSWORD = 'top-secret!'

OPENSTACK_ADMIN_TOKEN = "999888777666"
OPENSTACK_KEYSTONE_URL = "http://localhost:8080/v2.0/"

# If you have external monitoring links
EXTERNAL_MONITORING = [
    ['Nagios','http://foo.com'],
    ['Ganglia','http://bar.com'],
]

# If you do not have external monitoring links
# EXTERNAL_MONITORING = []

TOTAL_CLOUD_RAM_GB = 10
