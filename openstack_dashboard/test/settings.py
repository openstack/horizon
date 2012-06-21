import os

from horizon.tests.testsettings import *
from horizon.utils.secret_key import generate_or_read_from_file

TEST_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_PATH = os.path.abspath(os.path.join(TEST_DIR, ".."))

SECRET_KEY = generate_or_read_from_file(os.path.join(TEST_DIR,
                                                     '.secret_key_store'))
ROOT_URLCONF = 'openstack_dashboard.urls'
TEMPLATE_DIRS = (os.path.join(ROOT_PATH, 'templates'),)
STATICFILES_DIRS = (os.path.join(ROOT_PATH, 'static'),)
INSTALLED_APPS += ('openstack_dashboard',)
