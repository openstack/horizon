# The name of the panel to be added to HORIZON_CONFIG. Required.
PANEL = 'nonloading_panel'
# The name of the dashboard the PANEL associated with. Required.
PANEL_DASHBOARD = 'admin'
# The name of the panel group the PANEL is associated with.
PANEL_GROUP = 'admin'

# Python panel class of the PANEL to be added.
ADD_PANEL = \
    'openstack_dashboard.test.test_panels.nonloading_panel.panel.NonloadingPanel'

# A list of Django applications to be prepended to ``INSTALLED_APPS``
ADD_INSTALLED_APPS = ['openstack_dashboard.test.test_panels.nonloading_panel']
