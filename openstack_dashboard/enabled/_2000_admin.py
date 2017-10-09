# The slug of the dashboard to be added to HORIZON['dashboards']. Required.
DASHBOARD = 'admin'

# A list of applications to be added to INSTALLED_APPS.
ADD_INSTALLED_APPS = [
    'openstack_dashboard.dashboards.admin',
]

ADD_ANGULAR_MODULES = [
]

AUTO_DISCOVER_STATIC_FILES = True
