# The slug of the panel to be added to HORIZON_CONFIG. Required.
PANEL = 'overview'
# The slug of the dashboard the PANEL associated with. Required.
PANEL_DASHBOARD = 'admin'
# The slug of the panel group the PANEL is associated with.
PANEL_GROUP = 'default'
# If set, it will update the default panel of the PANEL_DASHBOARD.
DEFAULT_PANEL = 'overview'

# Python panel class of the PANEL to be added.
ADD_PANEL = 'openstack_dashboard.dashboards.admin.overview.panel.Overview'
