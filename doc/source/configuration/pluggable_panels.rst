.. _pluggable-settings-label:

===========================
Pluggable Panels and Groups
===========================

Introduction
============

Horizon allows dashboards, panels and panel groups to be added without
modifying the default settings. Pluggable settings are a mechanism to allow
settings to be stored in separate files.  Those files are read at startup and
used to modify the default settings.

The default location for the dashboard configuration files is
``openstack_dashboard/enabled``, with another directory,
``openstack_dashboard/local/enabled`` for local overrides. Both sets of files
will be loaded, but the settings in ``openstack_dashboard/local/enabled`` will
overwrite the default ones. The settings are applied in alphabetical order of
the filenames. If the same dashboard has configuration files in ``enabled`` and
``local/enabled``, the local name will be used. Note, that since names of
python modules can't start with a digit, the files are usually named with a
leading underscore and a number, so that you can control their order easily.

General Pluggbale Settings
==========================

Before we describe the specific use cases, the following keys can be used in
any pluggable settings file:

``ADD_EXCEPTIONS``
------------------

.. versionadded:: 2014.1(Icehouse)

A dictionary of exception classes to be added to ``HORIZON['exceptions']``.

``ADD_INSTALLED_APPS``
----------------------

.. versionadded:: 2014.1(Icehouse)

A list of applications to be prepended to ``INSTALLED_APPS``.
This is needed to expose static files from a plugin.

``ADD_ANGULAR_MODULES``
-----------------------

.. versionadded:: 2014.2(Juno)

A list of AngularJS modules to be loaded when Angular bootstraps. These modules
are added as dependencies on the root Horizon application ``horizon``.

``ADD_JS_FILES``
----------------

.. versionadded:: 2014.2(Juno)

A list of javascript source files to be included in the compressed set of files
that are loaded on every page. This is needed for AngularJS modules that are
referenced in ``ADD_ANGULAR_MODULES`` and therefore need to be included in
every page.

``ADD_JS_SPEC_FILES``
---------------------

.. versionadded:: 2015.1(Kilo)

A list of javascript spec files to include for integration with the Jasmine
spec runner. Jasmine is a behavior-driven development framework for testing
JavaScript code.

``ADD_SCSS_FILES``
------------------

.. versionadded:: 8.0.0(Liberty)

A list of scss files to be included in the compressed set of files that are
loaded on every page. We recommend one scss file per dashboard, use @import if
you need to include additional scss files for panels.


``ADD_XSTATIC_MODULES``
-----------------------

.. versionadded:: 14.0.0(Rocky)

A list of xstatic modules containing javascript and scss files to be included
in the compressed set of files that are loaded on every page. Related files
specified in ``ADD_XSTATIC_MODULES`` do not need to be included in
``ADD_JS_FILES``. This option expects a list of tuples, each consists of
a xstatic module and a list of javascript files to be loaded if any.
For more details, please check the comment of ``BASE_XSTATIC_MODULES``
in openstack_dashboard/utils/settings.py.

Example:

.. code-block:: python

   ADD_XSTATIC_MODULES = [
       ('xstatic.pkg.foo', ['foo.js']),
       ('xstatic.pkg.bar', None),
   ]

.. _auto_discover_static_files:

``AUTO_DISCOVER_STATIC_FILES``
------------------------------

.. versionadded:: 8.0.0(Liberty)

If set to ``True``, JavaScript files and static angular html template files
will be automatically discovered from the `static` folder in each apps listed
in ADD_INSTALLED_APPS.

JavaScript source files will be ordered based on naming convention: files with
extension `.module.js` listed first, followed by other JavaScript source files.

JavaScript files for testing will also be ordered based on naming convention:
files with extension `.mock.js` listed first, followed by files with extension
`.spec.js`.

If ADD_JS_FILES and/or ADD_JS_SPEC_FILES are also specified, files manually
listed there will be appended to the auto-discovered files.

``DISABLED``
------------

.. versionadded:: 2014.1(Icehouse)

If set to ``True``, this settings file will not be added to the settings.

``EXTRA_STEPS``
---------------

.. versionadded:: 14.0.0(Rocky)

Extra workflow steps can be added to a workflow in horizon or other
horizon plugins by using this setting. Extra steps will be shown after
default steps defined in a corresponding workflow.

This is a dict setting. A key of the dict specifies a workflow which extra
step(s) are added. The key must match a full class name of the target workflow.

A value of the dict is a list of full name of an extra step classes (where a
module name and a class name must be delimiteed by a period). Steps specified
via ``EXTRA_STEPS`` will be displayed in the order of being registered.

Example:

.. code-block:: python

   EXTRA_STEPS = {
       'openstack_dashboard.dashboards.identity.projects.workflows.UpdateQuota':
       (
           ('openstack_dashboard.dashboards.identity.projects.workflows.'
            'UpdateVolumeQuota'),
           ('openstack_dashboard.dashboards.identity.projects.workflows.'
            'UpdateNetworkQuota'),
       ),
   }

``EXTRA_TABS``
--------------

.. versionadded:: 14.0.0(Rocky)

Extra tabs can be added to a tab group implemented in horizon or other
horizon plugins by using this setting. Extra tabs will be shown after
default tabs defined in a corresponding tab group.

This is a dict setting. A key of the dict specifies a tab group which extra
tab(s) are added. The key must match a full class name of the target tab group.

A value of the dict is a list of full name of an extra tab classes (where a
module name and a class name must be delimiteed by a period). Tabs specified
via ``EXTRA_TABS`` will be displayed in the order of being registered.

There might be cases where you would like to specify the order of the extra
tabs as multiple horizon plugins can register extra tabs. You can specify a
priority of each tab in ``EXTRA_TABS`` by using a tuple of priority and a tab
class as an element of a dict value instead of a full name of an extra tab.
Priority is an integer of a tab and a tab with a lower value will be displayed
first. If a priority of an extra tab is omitted, ``0`` is assumed as a priority.

Example:

.. code-block:: python

   EXTRA_TABS = {
       'openstack_dashboard.dashboards.project.networks.tabs.NetworkDetailsTabs': (
           'openstack_dashboard.dashboards.project.networks.subnets.tabs.SubnetsTab',
           'openstack_dashboard.dashboards.project.networks.ports.tabs.PortsTab',
       ),
   }

Example (with priority):

.. code-block:: python

   EXTRA_TABS = {
       'openstack_dashboard.dashboards.project.networks.tabs.NetworkDetailsTabs': (
           (1, 'openstack_dashboard.dashboards.project.networks.subnets.tabs.SubnetsTab'),
           (2, 'openstack_dashboard.dashboards.project.networks.ports.tabs.PortsTab'),
       ),
   }

``UPDATE_HORIZON_CONFIG``
-------------------------

.. versionadded:: 2014.2(Juno)

A dictionary of values that will replace the values in ``HORIZON_CONFIG``.


Pluggable Settings for Dashboards
=================================

.. versionadded:: 2014.1(Icehouse)

The following keys are specific to registering a dashboard:


``DASHBOARD``
-------------

.. versionadded:: 2014.1(Icehouse)

The slug of the dashboard to be added to ``HORIZON['dashboards']``. Required.

``DEFAULT``
-----------

.. versionadded:: 2014.1(Icehouse)

If set to ``True``, this dashboard will be set as the default dashboard.


Examples
--------

To disable a dashboard locally, create a file
``openstack_dashboard/local/enabled/_40_dashboard-name.py`` with the following
content::

    DASHBOARD = '<dashboard-name>'
    DISABLED = True

To add a Tuskar-UI (Infrastructure) dashboard, you have to install it, and then
create a file ``openstack_dashboard/local/enabled/_50_tuskar.py`` with::

    from tuskar_ui import exceptions

    DASHBOARD = 'infrastructure'
    ADD_INSTALLED_APPS = [
        'tuskar_ui.infrastructure',
    ]
    ADD_EXCEPTIONS = {
        'recoverable': exceptions.RECOVERABLE,
        'not_found': exceptions.NOT_FOUND,
        'unauthorized': exceptions.UNAUTHORIZED,
    }


Pluggable Settings for Panels
=============================

.. versionadded:: 2014.1(Icehouse)

The following keys are specific to registering or removing a panel:

``PANEL``
---------

.. versionadded:: 2014.1(Icehouse)

The slug of the panel to be added to ``HORIZON_CONFIG``. Required.

``PANEL_DASHBOARD``
-------------------

.. versionadded:: 2014.1(Icehouse)

The slug of the dashboard the ``PANEL`` associated with. Required.


``PANEL_GROUP``
---------------

.. versionadded:: 2014.1(Icehouse)

The slug of the panel group the ``PANEL`` is associated with. If you want the
panel to show up without a panel group, use the panel group "default".

``DEFAULT_PANEL``
-----------------

.. versionadded:: 2014.1(Icehouse)

If set, it will update the default panel of the ``PANEL_DASHBOARD``.

``ADD_PANEL``
-------------

.. versionadded:: 2014.1(Icehouse)

Python panel class of the ``PANEL`` to be added.

``REMOVE_PANEL``
----------------

.. versionadded:: 2014.1(Icehouse)

If set to ``True``, the PANEL will be removed from PANEL_DASHBOARD/PANEL_GROUP.


Examples
--------

To add a new panel to the Admin panel group in Admin dashboard, create a file
``openstack_dashboard/local/enabled/_60_admin_add_panel.py`` with the following
content::

    PANEL = 'plugin_panel'
    PANEL_DASHBOARD = 'admin'
    PANEL_GROUP = 'admin'
    ADD_PANEL = 'test_panels.plugin_panel.panel.PluginPanel'

To remove Info panel from Admin panel group in Admin dashboard locally, create
a file ``openstack_dashboard/local/enabled/_70_admin_remove_panel.py`` with
the following content::

    PANEL = 'info'
    PANEL_DASHBOARD = 'admin'
    PANEL_GROUP = 'admin'
    REMOVE_PANEL = True

To change the default panel of Admin dashboard to Instances panel, create a
file ``openstack_dashboard/local/enabled/_80_admin_default_panel.py`` with the
following content::

    PANEL = 'instances'
    PANEL_DASHBOARD = 'admin'
    PANEL_GROUP = 'admin'
    DEFAULT_PANEL = 'instances'

Pluggable Settings for Panel Groups
===================================

.. versionadded:: 2014.1(Icehouse)


The following keys are specific to registering a panel group:

``PANEL_GROUP``
---------------

.. versionadded:: 2014.1(Icehouse)

The slug of the panel group to be added to ``HORIZON_CONFIG``. Required.

``PANEL_GROUP_NAME``
--------------------

.. versionadded:: 2014.1(Icehouse)

The display name of the PANEL_GROUP. Required.

``PANEL_GROUP_DASHBOARD``
-------------------------

.. versionadded:: 2014.1(Icehouse)

The slug of the dashboard the ``PANEL_GROUP`` associated with. Required.



Examples
--------

To add a new panel group to the Admin dashboard, create a file
``openstack_dashboard/local/enabled/_90_admin_add_panel_group.py`` with the
following content::

    PANEL_GROUP = 'plugin_panel_group'
    PANEL_GROUP_NAME = 'Plugin Panel Group'
    PANEL_GROUP_DASHBOARD = 'admin'
