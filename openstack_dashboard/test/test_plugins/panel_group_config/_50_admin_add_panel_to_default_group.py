# The name of the panel to be added to HORIZON_CONFIG. Required.
PANEL = 'another_panel'
# The name of the dashboard the PANEL associated with. Required.
PANEL_DASHBOARD = 'admin'
# The name of the panel group the PANEL is associated with.
PANEL_GROUP = 'default'

# Python panel class of the PANEL to be added.
ADD_PANEL = \
    'openstack_dashboard.test.test_panels.another_panel.panel.AnotherPanel'
