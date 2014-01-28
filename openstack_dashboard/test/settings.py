import os

from horizon.test.settings import *  # noqa
from horizon.utils import secret_key

from openstack_dashboard import exceptions


TEST_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_PATH = os.path.abspath(os.path.join(TEST_DIR, ".."))

SECRET_KEY = secret_key.generate_or_read_from_file(
    os.path.join(TEST_DIR, '.secret_key_store'))
ROOT_URLCONF = 'openstack_dashboard.urls'
TEMPLATE_DIRS = (
    os.path.join(TEST_DIR, 'templates'),
)

TEMPLATE_CONTEXT_PROCESSORS += (
    'openstack_dashboard.context_processors.openstack',
)

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
    'openstack_dashboard.dashboards.project',
    'openstack_dashboard.dashboards.admin',
    'openstack_dashboard.dashboards.settings',
    # If the profile_support config is turned on in local_settings
    # the "router" dashboard will be enabled which can be used to
    # create and use profiles with networks and instances. In which case
    # using run_tests will require the registration of the "router" dashboard.
    # TODO (absubram): Need to make this permanent when a better solution
    # for run_tests is implemented to use with and without the n1k sub-plugin.
    #'openstack_dashboard.dashboards.router',
)

AUTHENTICATION_BACKENDS = ('openstack_auth.backend.KeystoneBackend',)

SITE_BRANDING = 'OpenStack'

HORIZON_CONFIG = {
    'dashboards': ('project', 'admin', 'settings',),
    # If the profile_support config is turned on in local_settings
    # the "router" dashboard will be enabled which can be used to
    # create and use profiles with networks and instances. In which case
    # using run_tests will require the registration of the "router" dashboard.
    # TODO (absubram): Need to make this permanent when a better solution
    # for run_tests is implemented to use with and without the n1k sub-plugin.
    #'openstack_dashboard.dashboards.router',
    #'dashboards': ('project', 'admin', 'settings', 'router',),
    'default_dashboard': 'project',
    "password_validator": {
        "regex": '^.{8,18}$',
        "help_text": "Password must be between 8 and 18 characters."
    },
    'user_home': None,
    'help_url': "http://docs.openstack.org",
    'exceptions': {'recoverable': exceptions.RECOVERABLE,
                   'not_found': exceptions.NOT_FOUND,
                   'unauthorized': exceptions.UNAUTHORIZED},
}

# Set to True to allow users to upload images to glance via Horizon server.
# When enabled, a file form field will appear on the create image form.
# See documentation for deployment considerations.
HORIZON_IMAGES_ALLOW_UPLOAD = True

AVAILABLE_REGIONS = [
    ('http://localhost:5000/v2.0', 'local'),
    ('http://remote:5000/v2.0', 'remote'),
]

OPENSTACK_API_VERSIONS = {
    "identity": 3
}

OPENSTACK_KEYSTONE_URL = "http://localhost:5000/v2.0"
OPENSTACK_KEYSTONE_DEFAULT_ROLE = "Member"

OPENSTACK_KEYSTONE_MULTIDOMAIN_SUPPORT = True
OPENSTACK_KEYSTONE_DEFAULT_DOMAIN = 'test_domain'

OPENSTACK_KEYSTONE_BACKEND = {
    'name': 'native',
    'can_edit_user': True,
    'can_edit_group': True,
    'can_edit_project': True,
    'can_edit_domain': True,
    'can_edit_role': True
}

OPENSTACK_NEUTRON_NETWORK = {
    'enable_lb': True,
    'enable_firewall': True,
    'enable_quotas': False,  # Enabled in specific tests only
    'enable_vpn': True
}

OPENSTACK_HYPERVISOR_FEATURES = {
    'can_set_mount_point': True,
}

OPENSTACK_IMAGE_BACKEND = {
    'image_formats': [
        ('', ''),
        ('aki', 'AKI - Amazon Kernel Image'),
        ('ami', 'AMI - Amazon Machine Image'),
        ('ari', 'ARI - Amazon Ramdisk Image'),
        ('iso', 'ISO - Optical Disk Image'),
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

POLICY_FILES_PATH = os.path.join(ROOT_PATH, "conf")
POLICY_FILES = {
    'identity': 'keystone_policy.json',
    'compute': 'nova_policy.json'
}
