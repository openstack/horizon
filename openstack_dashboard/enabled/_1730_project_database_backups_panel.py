# The slug of the panel to be added to HORIZON_CONFIG. Required.
PANEL = 'database_backups'
# The slug of the dashboard the PANEL associated with. Required.
PANEL_DASHBOARD = 'project'
# The slug of the panel group the PANEL is associated with.
PANEL_GROUP = 'database'

# Python panel class of the PANEL to be added.
ADD_PANEL = ('openstack_dashboard.contrib.trove.'
             'content.database_backups.panel.Backups')
