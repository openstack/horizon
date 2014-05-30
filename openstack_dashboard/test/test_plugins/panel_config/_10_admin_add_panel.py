# The name of the panel to be added to HORIZON_CONFIG. Required.
PANEL = 'plugin_panel'
# The name of the dashboard the PANEL associated with. Required.
PANEL_DASHBOARD = 'admin'
# The name of the panel group the PANEL is associated with.
PANEL_GROUP = 'admin'

# Python panel class of the PANEL to be added.
ADD_PANEL = \
    'openstack_dashboard.test.test_panels.plugin_panel.panel.PluginPanel'

# A list of Django applications to be prepended to ``INSTALLED_APPS``
ADD_INSTALLED_APPS = ['openstack_dashboard.test.test_panels.plugin_panel']

# A list of AngularJS modules to be loaded when Angular bootstraps.
ADD_ANGULAR_MODULES = ['testAngularModule']

# A list of javascript files to be included in the compressed set of files
ADD_JS_FILES = ['plugin_panel/plugin_module.js']
