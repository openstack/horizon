import os

from horizon.tests.testsettings import *

TEST_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_PATH = os.path.abspath(os.path.join(TEST_DIR, ".."))

ROOT_URLCONF = 'openstack_dashboard.urls'
TEMPLATE_DIRS = (os.path.join(ROOT_PATH, 'templates'),)
STATICFILES_DIRS = (os.path.join(ROOT_PATH, 'static'),)
INSTALLED_APPS += ('openstack_dashboard',)
