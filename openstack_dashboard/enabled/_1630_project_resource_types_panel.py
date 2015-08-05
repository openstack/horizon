# The slug of the panel to be added to HORIZON_CONFIG. Required.
PANEL = 'stacks.resource_types'
# The slug of the dashboard the PANEL associated with. Required.
PANEL_DASHBOARD = 'project'
# The slug of the panel group the PANEL is associated with.
PANEL_GROUP = 'orchestration'

# Python panel class of the PANEL to be added.
ADD_PANEL = ('openstack_dashboard.dashboards.project.'
             'stacks.resource_types.panel.ResourceTypes')
