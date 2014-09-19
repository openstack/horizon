# The name of the dashboard to be added to HORIZON['dashboards']. Required.
DASHBOARD = 'admin'
DISABLED = True
# A list of applications to be added to INSTALLED_APPS.
ADD_INSTALLED_APPS = [
    'openstack_dashboard.dashboards.admin',
]
