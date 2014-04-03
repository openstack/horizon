==================================
Horizon Settings and Configuration
==================================

Introduction
============

Horizon's settings tend to fall into three categories:

* Horizon configuration options (contained in the ``HORIZON_CONFIG`` dict)
  which are not OpenStack-specific and pertain only to the core framework.
* OpenStack-related settings which pertain to other projects/services and
  are generally prefixed with ``OPENSTACK_`` in the settings file.
* Django settings (including common plugins like ``django-compressor``) which
  can be (and should be) read about in their respective documentation.

What follows is an overview of the Horizon and OpenStack-specific settings
and a few notes on the Django-related settings.

.. note::

    Prior to the Essex release of Horizon there were settings which controlled
    whether features such as Object Storage/Swift or Networking/Neutron would be
    enabled in the OpenStack Dashboard. This code has long since been removed
    and those pre-Essex settings have no impact now.

    In Essex and later, the Service Catalog returned by the Identity Service
    after a user has successfully authenticated determines the dashboards and
    panels that will be available within the OpenStack Dashboard. If you are not
    seeing a particular service you expected make sure your Service Catalog is
    configured correctly.

Horizon Settings
================

The following options are available in order to configure/customize the
behavior of your Horizon installation. All of them are contained in the
``HORIZON_CONFIG`` dictionary.

.. _dashboards:

``dashboards``
--------------

Default: ``None``

Horizon Dashboards are automatically discovered in the following way:

* By traversing Django's list of
  `INSTALLED_APPS <https://docs.djangoproject.com/en/1.4/ref/settings/#std:setting-INSTALLED_APPS>`_
  and importing any files that have the name ``"dashboard.py"`` and include
  code to register themselves as a Horizon dashboard.
* By adding a configuration file to the ``openstack_dashboard/local/enabled``
  directory (for more information see :ref:`pluggable-settings-label`).

By default, these dashboards are ordered alphabetically.
However, if a list of dashboard slugs is provided in this setting, the supplied
ordering is applied to the list of discovered dashboards. If the list of
dashboard slugs is shorter than the number of discovered dashboards, the
remaining dashboards are appended in alphabetical order.

The dashboards listed must be in a Python module which
is included in the ``INSTALLED_APPS`` list and on the Python path.

``default_dashboard``
---------------------

Default: ``None``

The slug of the dashboard which should act as the first-run/fallback dashboard
whenever a user logs in or is otherwise redirected to an ambiguous location.

``user_home``
-------------

Default: ``settings.LOGIN_REDIRECT_URL``

This can be either a literal URL path (such as the default), or Python's
dotted string notation representing a function which will evaluate what URL
a user should be redirected to based on the attributes of that user.

``ajax_queue_limit``
--------------------

Default: ``10``

The maximum number of simultaneous AJAX connections the dashboard may try
to make. This is particularly relevant when monitoring a large number of
instances, volumes, etc. which are all actively trying to update/change state.

``ajax_poll_interval``
----------------------

Default: ``2500``

How frequently resources in transition states should be polled for updates,
expressed in milliseconds.

``help_url``
------------

Default: ``None``

If provided, a "Help" link will be displayed in the site header which links
to the value of this settings (ideally a URL containing help information).

``exceptions``
--------------

Default: ``{'unauthorized': [], 'not_found': [], 'recoverable': []}``

A dictionary containing classes of exceptions which Horizon's centralized
exception handling should be aware of.

``password_validator``
----------------------

Default: ``{'regex': '.*', 'help_text': _("Password is not accepted")}``

A dictionary containing a regular expression which will be used for password
validation and help text which will be displayed if the password does not
pass validation. The help text should describe the password requirements if
there are any.

This setting allows you to set rules for passwords if your organization
requires them.

``password_autocomplete``
-------------------------

Default: ``"on"``

Controls whether browser autocompletion should be enabled on the login form.
Valid values are ``"on"`` and ``"off"``.

``simple_ip_management``
------------------------

Default: ``True``

Enable or disable simplified floating IP address management.

"Simple" floating IP address management means that the user does not ever have
to select the specific IP addresses they wish to use, and the process of
allocating an IP and assigning it to an instance is one-click.

The "advanced" floating IP management allows users to select the floating IP
pool from which the IP should be allocated and to select a specific IP address
when associating one with an instance.

.. note::

    Currently "simple" floating IP address management is not compatible with
    Neutron. There are two reasons for this. First, Neutron does not support
    the default floating IP pool at the moment. Second, a Neutron floating IP
    can be associated with each VIF and we need to check whether there is only
    one VIF for an instance to enable simple association support.

OpenStack Settings (Partial)
============================

The following settings inform the OpenStack Dashboard of information about the
other OpenStack projects which are part of this cloud and control the behavior
of specific dashboards, panels, API calls, etc.

Most of the following settings are defined in
 ``openstack_dashboard/local/local_settings.py``, which should be copied from
 ``openstack_dashboard/local/local_settings.py.example``.

``API_RESULT_LIMIT``
--------------------

Default: ``1000``

The maximum number of objects (e.g. Swift objects or Glance images) to display
on a single page before providing a paging element (a "more" link) to paginate
results.

``API_RESULT_PAGE_SIZE``
------------------------

Default: ``20``

Similar to ``API_RESULT_LIMIT``. This setting currently only controls the
Glance image list page size. It will be removed in a future version.


``AVAILABLE_REGIONS``
---------------------

Default: ``None``

A tuple of tuples which define multiple regions. The tuple format is
``('http://{{keystone_host}}:5000/v2.0', '{{region_name}}')``. If any regions
are specified the login form will have a dropdown selector for authenticating
to the appropriate region, and there will be a region switcher dropdown in
the site header when logged in.

If you do not have multiple regions you should use the ``OPENSTACK_HOST`` and
``OPENSTACK_KEYSTONE_URL`` settings instead.

``CREATE_INSTANCE_FLAVOR_SORT``
-------------------------------

Default: ``{'key':'ram'}``

When launching a new instance the default flavor is sorted by RAM usage in
ascending order.
You can customize the sort order by: id, name, ram, disk and vcpus.
Additionally, you can insert any custom callback function,
see the description in local_settings.py.example for more information.

This example sorts flavors by vcpus in descending order::

    CREATE_INSTANCE_FLAVOR_SORT = {
         'key':'vcpus',
         'reverse': True,
    }

``IMAGES_LIST_FILTER_TENANTS``
------------------------------

Default: ``None``

A list of dictionaries to add optional categories to the image filters
in the Images & Snapshots panel, based on project ownership.

Each dictionary should contain a `tenant` attribute with the project
id, and optionally a `text` attribute specifying the category name, and
an `icon` attribute that displays an icon in the filter button. The
icon names are based on the default icon theme provided by Bootstrap.

Example: ``[{'text': 'Official', 'tenant': '27d0058849da47c896d205e2fc25a5e8', 'icon': 'icon-ok'}]``

``OPENSTACK_ENABLE_PASSWORD_RETRIEVE``
--------------------------------------

Default: ``"False"``

When set, enables the instance action "Retrieve password" allowing password retrieval
from metadata service.


``OPENSTACK_ENDPOINT_TYPE``
---------------------------

Default: ``"publicURL"``

A string which specifies the endpoint type to use for the endpoints in the
Keystone service catalog. The default value for all services except for identity is ``"publicURL"`` . The default value for the identity service is ``"internalURL"``.


``OPENSTACK_HOST``
------------------

Default: ``"127.0.0.1"``

The hostname of the Keystone server used for authentication if you only have
one region. This is often the *only* setting that needs to be set for a
basic deployment.


``OPENSTACK_HYPERVISOR_FEATURES``
---------------------------------

Default::

    {
        'can_set_mount_point': False,
        'can_set_password': False
    }

A dictionary containing settings which can be used to identify the
capabilities of the hypervisor for Nova.

The Xen Hypervisor has the ability to set the mount point for volumes attached
to instances (other Hypervisors currently do not). Setting
``can_set_mount_point`` to ``True`` will add the option to set the mount point
from the UI.

Setting ``can_set_password`` to ``True`` will enable the option to set
an administrator password when launching or rebuilding an instance.


``OPENSTACK_IMAGE_BACKEND``
---------------------------

Default::

    {
        'image_formats': [
            ('', ''),
            ('aki', _('AKI - Amazon Kernel Image')),
            ('ami', _('AMI - Amazon Machine Image')),
            ('ari', _('ARI - Amazon Ramdisk Image')),
            ('iso', _('ISO - Optical Disk Image')),
            ('qcow2', _('QCOW2 - QEMU Emulator')),
            ('raw', _('Raw')),
            ('vdi', _('VDI')),
            ('vhd', _('VHD')),
            ('vmdk', _('VMDK'))
        ]
    }

Used to customize features related to the image service, such as the list of
supported image formats.


``OPENSTACK_KEYSTONE_BACKEND``
------------------------------

Default: ``{'name': 'native', 'can_edit_user': True, 'can_edit_project': True}``

A dictionary containing settings which can be used to identify the
capabilities of the auth backend for Keystone.

If Keystone has been configured to use LDAP as the auth backend then set
``can_edit_user`` and ``can_edit_project`` to ``False`` and name to ``"ldap"``.


``OPENSTACK_KEYSTONE_DEFAULT_ROLE``
-----------------------------------

Default: ``"_member_"``

The name of the role which will be assigned to a user when added to a project.
This name must correspond to a role name in Keystone.


``OPENSTACK_KEYSTONE_URL``
--------------------------

Default: ``"http://%s:5000/v2.0" % OPENSTACK_HOST``

The full URL for the Keystone endpoint used for authentication. Unless you
are using HTTPS, running your Keystone server on a nonstandard port, or using
a nonstandard URL scheme you shouldn't need to touch this setting.


``OPENSTACK_NEUTRON_NETWORK``
-----------------------------

Default: ``{'enable_lb': False}``

A dictionary of settings which can be used to enable optional services provided
by neutron.  Currently only the load balancer service is available.


``OPENSTACK_SSL_CACERT``
------------------------

Default: ``None``

When unset or set to ``None`` the default CA certificate on the system is used
for SSL verification.

When set with the path to a custom CA certificate file, this overrides use of
the default system CA certificate. This custom certificate is used to verify all
connections to openstack services when making API calls.


``OPENSTACK_SSL_NO_VERIFY``
---------------------------

Default: ``False``

Disable SSL certificate checks in the OpenStack clients (useful for self-signed
certificates).


``POLICY_FILES``
----------------

Default: ``{'identity': 'keystone_policy.json', 'compute': 'nova_policy.json'}``

This should essentially be the mapping of the contents of ``POLICY_FILES_PATH``
to service types.  When policy.json files are added to ``POLICY_FILES_PATH``,
they should be included here too.


``POLICY_FILES_PATH``
---------------------

Default:  ``os.path.join(ROOT_PATH, "conf")``

Specifies where service based policy files are located.  These are used to
define the policy rules actions are verified against.

``SESSION_TIMEOUT``
-------------------

Default: ``"1800"``

Specifies the timespan in seconds inactivity, until a user is considered as
 logged out.

``FLAVOR_EXTRA_KEYS``
---------------------

Default::

    {
        'flavor_keys': [
            ('quota:read_bytes_sec', _('Quota: Read bytes')),
            ('quota:write_bytes_sec', _('Quota: Write bytes')),
            ('quota:cpu_quota', _('Quota: CPU')),
            ('quota:cpu_period', _('Quota: CPU period')),
            ('quota:inbound_average', _('Quota: Inbound average')),
            ('quota:outbound_average', _('Quota: Outbound average'))
        ]
    }

Used to customize flavor extra specs keys


Django Settings (Partial)
=========================

.. warning::

    This is not meant to be anywhere near a complete list of settings for
    Django. You should always consult the upstream documentation, especially
    with regards to deployment considerations and security best-practices.

There are a few key settings you should be aware of for development and the
most basic of deployments. Further recommendations can be found in the
Deploying Horizon section of this documentation.

``ALLOWED_HOSTS``
-----------------

Default: ``['localhost']``

This list should contain names (or IP addresses) of the host
running the dashboard; if it's being accessed via name, the
DNS name (and probably short-name) should be added, if it's accessed via
IP address, that should be added. The setting may contain more than one entry.



``DEBUG`` and ``TEMPLATE_DEBUG``
--------------------------------

Default: ``True``

Controls whether unhandled exceptions should generate a generic 500 response
or present the user with a pretty-formatted debug information page.

This setting should **always** be set to ``False`` for production deployments
as the debug page can display sensitive information to users and attackers
alike.

``SECRET_KEY``
--------------

This should absolutely be set to a unique (and secret) value for your
deployment. Unless you are running a load-balancer with multiple Horizon
installations behind it, each Horizon instance should have a unique secret key.

The ``local_settings.py.example`` file includes a quick-and-easy way to
generate a secret key for a single installation.

``SECURE_PROXY_SSL_HEADER``, ``CSRF_COOKIE_SECURE`` and ``SESSION_COOKIE_SECURE``
---------------------------------------------------------------------------------

These three settings should be configured if you are deploying Horizon with
SSL. The values indicated in the default ``local_settings.py.example`` file
are generally safe to use.

.. _pluggable-settings-label:

Pluggable Settings for Dashboards
=================================

Many dashboards may require their own modifications to the settings, and their
installation would therefore require modifying the settings file. This is not
optimal, so the dashboards can provide the settings that they require in a
separate file. Those files are read at startup and used to modify the default
settings.

The default location for the dashboard configuration files is
``openstack_dashboard/enabled``, with another directory,
``openstack_dashboard/local/enabled`` for local overrides. Both sets of files
will be loaded, but the settings in ``openstack_dashboard/local/enabled`` will
overwrite the default ones. The settings are applied in alphabetical order of
the filenames. If the same dashboard has configuration files in ``enabled`` and
``local/enabled``, the local name will be used. Note, that since names of
python modules can't start with a digit, the files are usually named with a
leading underscore and a number, so that you can control their order easily.

The files contain following keys:

``DASHBOARD``
-------------

The name of the dashboard to be added to ``HORIZON['dashboards']``. Required.

``DEFAULT``
-----------

If set to ``True``, this dashboard will be set as the default dashboard.

``ADD_EXCEPTIONS``
------------------

A dictionary of exception classes to be added to ``HORIZON['exceptions']``.

``ADD_INSTALLED_APPS``
----------------------

A list of applications to be prepended to ``INSTALLED_APPS``.

``DISABLED``
------------

If set to ``True``, this dashboard will not be added to the settings.

Examples
--------

To disable the Router dashboard locally, create a file
``openstack_dashboard/local/enabled/_40_router.py`` with the following
content::

    DASHBOARD = 'router'
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

Panels customization can be made by providing a custom python module that
contains python code to add or remove panel to/from the dashboard. This
requires altering the settings file. For panels provided by third-party,
making this changes to add the panel is challenging. Panel configuration
files can now be dropped to a specified location and it will be read at startup
to alter the dashboard configuration.

The default location for the panel configuration files is
``openstack_dashboard/enabled``, with another directory,
``openstack_dashboard/local/enabled`` for local overrides. Both sets of files
will be loaded, but the settings in ``openstack_dashboard/local/enabled`` will
overwrite the default ones. The settings are applied in alphabetical order of
the filenames. If the same panel has configuration files in ``enabled`` and
``local/enabled``, the local name will be used. Note, that since names of
python modules can't start with a digit, the files are usually named with a
leading underscore and a number, so that you can control their order easily.

The files contain following keys:

``PANEL``
---------

The name of the panel to be added to ``HORIZON_CONFIG``. Required.

``PANEL_DASHBOARD``
-------------------

The name of the dashboard the ``PANEL`` associated with. Required.


``PANEL_GROUP``
---------------

The name of the panel group the ``PANEL`` is associated with.

``DEFAULT_PANEL``
-----------------

If set, it will update the default panel of the ``PANEL_DASHBOARD``.

``ADD_PANEL``
-------------

Python panel class of the ``PANEL`` to be added.

``REMOVE_PANEL``
----------------

If set to ``True``, the PANEL will be removed from PANEL_DASHBOARD/PANEL_GROUP.

``DISABLED``
------------

If set to ``True``, this panel configuration will be skipped.

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

To change the default panel of Admin dashboard to Instances panel, create a file
``openstack_dashboard/local/enabled/_80_admin_default_panel.py`` with the
following content::

    PANEL = 'instances'
    PANEL_DASHBOARD = 'admin'
    PANEL_GROUP = 'admin'
    DEFAULT_PANEL = 'instances'

Pluggable Settings for Panel Groups
===================================

To organize the panels created from the pluggable settings, there is also
a way to create panel group though configuration file. This creates an empty
panel group to act as placeholder for the panels that can be created later.

The default location for the panel group configuration files is
``openstack_dashboard/enabled``, with another directory,
``openstack_dashboard/local/enabled`` for local overrides. Both sets of files
will be loaded, but the settings in ``openstack_dashboard/local/enabled`` will
overwrite the default ones. The settings are applied in alphabetical order of
the filenames. If the same panel has configuration files in ``enabled`` and
``local/enabled``, the local name will be used. Note, that since names of
python modules can't start with a digit, the files are usually named with a
leading underscore and a number, so that you can control their order easily.

When writing configuration files to create panels and panels group, make sure
that the panel group configuration file is loaded first because the panel
configuration might be referencing it. This can be achieved by providing a file
name that will go before the panel configuration file when the files are sorted
alphabetically.

The files contain following keys:

``PANEL_GROUP``
---------------

The name of the panel group to be added to ``HORIZON_CONFIG``. Required.

``PANEL_GROUP_NAME``
--------------------

The display name of the PANEL_GROUP. Required.

``PANEL_GROUP_DASHBOARD``
-------------------------

The name of the dashboard the ``PANEL_GROUP`` associated with. Required.

``DISABLED``
------------

If set to ``True``, this panel configuration will be skipped.

Examples
--------

To add a new panel group to the Admin dashboard, create a file
``openstack_dashboard/local/enabled/_90_admin_add_panel_group.py`` with the
following content::

    PANEL_GROUP = 'plugin_panel_group'
    PANEL_GROUP_NAME = 'Plugin Panel Group'
    PANEL_GROUP_DASHBOARD = 'admin'
