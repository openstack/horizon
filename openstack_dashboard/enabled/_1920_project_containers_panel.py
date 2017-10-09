# The slug of the panel to be added to HORIZON_CONFIG. Required.
PANEL = 'containers'
# The slug of the dashboard the PANEL associated with. Required.
PANEL_DASHBOARD = 'project'
# The slug of the panel group the PANEL is associated with.
PANEL_GROUP = 'object_store'

# Python panel class of the PANEL to be added.
ADD_PANEL = ('openstack_dashboard.dashboards.project.'
             'containers.panel.Containers')

DISABLED = False

ADD_SCSS_FILES = [
    'dashboard/project/containers/_containers.scss',
]
