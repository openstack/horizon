==========================
Settings and Configuration
==========================

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

.. warning::

   In OpenStack Dashboard configuration, we suggest **NOT** to use this
   setting. Please specify the order of dashboard using the
   :ref:`pluggable-settings-label`.

   Both the pluggable dashboard mechanism (OpenStack Dashboard default) and
   this setting ``dashboard`` configure the order of dashboards and
   the setting ``dashboard`` precedes the pluggable dashboard mechanism.
   Specifying the order in two places may cause confusion.
   Please use this parameter only when the pluggable config is not used.

.. versionadded:: 2012.1(Essex)

Default: ``None``

Horizon Dashboards are automatically discovered in the following way:

* By adding a configuration file to the ``openstack_dashboard/local/enabled``
  directory (for more information see :ref:`pluggable-settings-label`).
  This is the default way in OpenStack Dashboard.
* By traversing Django's list of
  `INSTALLED_APPS <https://docs.djangoproject.com/en/1.4/ref/settings/#std:setting-INSTALLED_APPS>`_
  and importing any files that have the name ``"dashboard.py"`` and include
  code to register themselves as a Horizon dashboard.

By default, dashboards defined by ``openstack_dashboard/local/enabled`` are
displayed first in the alphabetical order of the config files, and then the
remaining dashboards discovered by traversing INSTALLED_APPS are displayed
in the alphabetical order.

If a list of ``dashboard`` slugs is provided in this setting, the supplied
ordering is applied to the list of discovered dashboards. If the list of
dashboard slugs is shorter than the number of discovered dashboards, the
remaining dashboards are appended in the default order described above.

The dashboards listed must be in a Python module which
is included in the ``INSTALLED_APPS`` list and on the Python path.

``default_dashboard``
---------------------

.. warning::

   In OpenStack Dashboard configuration, we suggest **NOT** to use this
   setting. Please specify the order of dashboard using the
   :ref:`pluggable-settings-label`.

   The default dashboard can be configured via both the pluggable
   dashboard mechanism (OpenStack Dashboard default) and this setting
   ``default_dashboard``, and if both are specified, the setting
   by the pluggable dashboard mechanism will be used.
   Specifying the default dashboard in two places may cause confusion.
   Please use this parameter only when the pluggable config is not used.

.. versionadded:: 2012.1(Essex)

Default: ``None``

The slug of the dashboard which should act as the first-run/fallback dashboard
whenever a user logs in or is otherwise redirected to an ambiguous location.

``user_home``
-------------

.. versionadded:: 2012.1(Essex)

Default: ``settings.LOGIN_REDIRECT_URL``

This can be either a literal URL path (such as the default), or Python's
dotted string notation representing a function which will evaluate what URL
a user should be redirected to based on the attributes of that user.

``ajax_queue_limit``
--------------------

.. versionadded:: 2012.1(Essex)

Default: ``10``

The maximum number of simultaneous AJAX connections the dashboard may try
to make. This is particularly relevant when monitoring a large number of
instances, volumes, etc. which are all actively trying to update/change state.

``ajax_poll_interval``
----------------------

.. versionadded:: 2012.1(Essex)

Default: ``2500``

How frequently resources in transition states should be polled for updates,
expressed in milliseconds.

``auto_fade_alerts``
--------------------

.. versionadded:: 2013.2(Havana)

Defaults: ``{'delay': [3000], 'fade_duration': [1500], 'types': []}``

If provided, will auto-fade the alert types specified. Valid alert types
include: ['alert-success', 'alert-info', 'alert-warning', 'alert-error']
Can also define the delay before the alert fades and the fade out duration.

``help_url``
------------

.. versionadded:: 2012.2(Folsom)

Default: ``None``

If provided, a "Help" link will be displayed in the site header which links
to the value of this settings (ideally a URL containing help information).

``exceptions``
--------------

.. versionadded:: 2012.1(Essex)

Default: ``{'unauthorized': [], 'not_found': [], 'recoverable': []}``

A dictionary containing classes of exceptions which Horizon's centralized
exception handling should be aware of. Based on these exception categories,
Horizon will handle the exception and display a message to the user.

``password_validator``
----------------------

.. versionadded:: 2012.1(Essex)

Default: ``{'regex': '.*', 'help_text': _("Password is not accepted")}``

A dictionary containing a regular expression which will be used for password
validation and help text which will be displayed if the password does not
pass validation. The help text should describe the password requirements if
there are any.

This setting allows you to set rules for passwords if your organization
requires them.

``password_autocomplete``
-------------------------

.. versionadded:: 2013.1(Grizzly)

Default: ``"on"``

Controls whether browser autocompletion should be enabled on the login form.
Valid values are ``"on"`` and ``"off"``.

``simple_ip_management``
------------------------

.. versionadded:: 2013.1(Grizzly)

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

``angular_modules``
-------------------------

Default: ``[]``

A list of AngularJS modules to be loaded when Angular bootstraps. These modules
are added as dependencies on the root Horizon application ``hz``.

``js_files``
-------------------------

Default: ``[]``

A list of javascript files to be included in the compressed set of files that are
loaded on every page. This is needed for AngularJS modules that are referenced in
``angular_modules`` and therefore need to be include in every page.


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

.. versionadded:: 2012.1(Essex)

Default: ``1000``

The maximum number of objects (e.g. Swift objects or Glance images) to display
on a single page before providing a paging element (a "more" link) to paginate
results.

``API_RESULT_PAGE_SIZE``
------------------------

.. versionadded:: 2012.2(Folsom)

Default: ``20``

Similar to ``API_RESULT_LIMIT``. This setting controls the number of items
to be shown per page if API pagination support for this exists.


``AVAILABLE_REGIONS``
---------------------

.. versionadded:: 2012.1(Essex)

Default: ``None``

A tuple of tuples which define multiple regions. The tuple format is
``('http://{{keystone_host}}:5000/v2.0', '{{region_name}}')``. If any regions
are specified the login form will have a dropdown selector for authenticating
to the appropriate region, and there will be a region switcher dropdown in
the site header when logged in.

If you do not have multiple regions you should use the ``OPENSTACK_HOST`` and
``OPENSTACK_KEYSTONE_URL`` settings instead.


``CONSOLE_TYPE``
----------------

.. versionadded:: 2013.2(Havana)

Default:  ``"AUTO"``

This settings specifies the type of in-browser VNC console used to access the
VMs.
Valid values are  ``"AUTO"``(default), ``"VNC"``, ``"SPICE"``, ``"RDP"``
and ``None`` (this latest value is available in version 2014.2(Juno) to allow
deactivating the in-browser console).


``CREATE_INSTANCE_FLAVOR_SORT``
-------------------------------

.. versionadded:: 2013.2(Havana)

Default: ``{'key':'ram'}``

When launching a new instance the default flavor is sorted by RAM usage in
ascending order.
You can customize the sort order by: id, name, ram, disk and vcpus.
Additionally, you can insert any custom callback function. You can also
provide a flag for reverse sort.
See the description in local_settings.py.example for more information.

This example sorts flavors by vcpus in descending order::

    CREATE_INSTANCE_FLAVOR_SORT = {
         'key':'vcpus',
         'reverse': True,
    }

``IMAGES_LIST_FILTER_TENANTS``
------------------------------

.. versionadded:: 2013.1(Grizzly)

Default: ``None``

A list of dictionaries to add optional categories to the image filters
in the Images & Snapshots panel, based on project ownership.

Each dictionary should contain a `tenant` attribute with the project
id, and optionally a `text` attribute specifying the category name, and
an `icon` attribute that displays an icon in the filter button. The
icon names are based on the default icon theme provided by Bootstrap.

Example: ``[{'text': 'Official', 'tenant': '27d0058849da47c896d205e2fc25a5e8', 'icon': 'icon-ok'}]``

``IMAGE_RESERVED_CUSTOM_PROPERTIES``
------------------------------------

.. versionadded:: 2014.2(Juno)

Default: ``[]``

A list of image custom property keys that should not be displayed in the
Update Metadata tree.

This setting can be used in the case where a separate panel is used for
managing a custom property or if a certain custom property should never be
edited.

``OPENSTACK_API_VERSIONS``
--------------------------

.. versionadded:: 2013.2(Havana)

Default::

    {
        "data_processing": 1.1,
        "identity": 2.0,
        "volume": 1
    }

Overrides for OpenStack API versions. Use this setting to force the
OpenStack dashboard to use a specific API version for a given service API.

.. note::

    The version should be formatted as it appears in the URL for the
    service API. For example, the identity service APIs have inconsistent
    use of the decimal point, so valid options would be "2.0" or "3".
    For example,
    OPENSTACK_API_VERSIONS = {
        "data_processing": 1.1,
        "identity": 3,
        "volume": 2
    }


``OPENSTACK_ENABLE_PASSWORD_RETRIEVE``
--------------------------------------

.. versionadded:: 2014.1(Icehouse)

Default: ``"False"``

When set, enables the instance action "Retrieve password" allowing password retrieval
from metadata service.


``OPENSTACK_ENDPOINT_TYPE``
---------------------------

.. versionadded:: 2012.1(Essex)

Default: ``"publicURL"``

A string which specifies the endpoint type to use for the endpoints in the
Keystone service catalog. The default value for all services except for identity is ``"publicURL"`` . The default value for the identity service is ``"internalURL"``.


``OPENSTACK_HOST``
------------------

.. versionadded:: 2012.1(Essex)

Default: ``"127.0.0.1"``

The hostname of the Keystone server used for authentication if you only have
one region. This is often the *only* setting that needs to be set for a
basic deployment.

.. _hypervisor-settings-label:

``OPENSTACK_HYPERVISOR_FEATURES``
---------------------------------

.. versionadded:: 2012.2(Folsom)

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

.. versionadded:: 2013.2(Havana)

Default::

    {
        'image_formats': [
            ('', _('Select format')),
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


``IMAGE_CUSTOM_PROPERTY_TITLES``
--------------------------------

.. versionadded:: 2014.1(Icehouse)

Default::

    {
        "architecture": _("Architecture"),
        "kernel_id": _("Kernel ID"),
        "ramdisk_id": _("Ramdisk ID"),
        "image_state": _("Euca2ools state"),
        "project_id": _("Project ID"),
        "image_type": _("Image Type")
    }

Used to customize the titles for image custom property attributes that
appear on image detail pages.


``HORIZON_IMAGES_ALLOW_UPLOAD``
--------------------------------

.. versionadded:: 2013.1(Grizzly)

Default: ``True``

If set to ``False``, this setting disables *local* uploads to prevent filling
up the disk on the dashboard server since uploads to the Glance image store
service tend to be particularly large - in the order of hundreds of megabytes
to multiple gigabytes.

.. note::

    This will not disable image creation altogether, as this setting does not
    affect images created by specifying an image location (URL) as the image source.


``OPENSTACK_KEYSTONE_BACKEND``
------------------------------

.. versionadded:: 2012.1(Essex)

Default: ``{'name': 'native', 'can_edit_user': True, 'can_edit_project': True}``

A dictionary containing settings which can be used to identify the
capabilities of the auth backend for Keystone.

If Keystone has been configured to use LDAP as the auth backend then set
``can_edit_user`` and ``can_edit_project`` to ``False`` and name to ``"ldap"``.


``OPENSTACK_KEYSTONE_DEFAULT_DOMAIN``
-------------------------------------

.. versionadded:: 2013.2(Havana)

Default: ``"Default"``

Overrides the default domain used when running on single-domain model
with Keystone V3. All entities will be created in the default domain.


``OPENSTACK_KEYSTONE_DEFAULT_ROLE``
-----------------------------------

.. versionadded:: 2011.3(Diablo)

Default: ``"_member_"``

The name of the role which will be assigned to a user when added to a project.
This name must correspond to a role name in Keystone.


``OPENSTACK_KEYSTONE_MULTIDOMAIN_SUPPORT``
------------------------------------------

.. versionadded:: 2013.2(Havana)

Default: ``False``

Set this to True if running on multi-domain model. When this is enabled, it
will require user to enter the Domain name in addition to username for login.


``OPENSTACK_KEYSTONE_URL``
--------------------------

.. versionadded:: 2011.3(Diablo)

Default: ``"http://%s:5000/v2.0" % OPENSTACK_HOST``

The full URL for the Keystone endpoint used for authentication. Unless you
are using HTTPS, running your Keystone server on a nonstandard port, or using
a nonstandard URL scheme you shouldn't need to touch this setting.


``OPENSTACK_CINDER_FEATURES``
-----------------------------

.. versionadded:: 2014.2(Juno)

Default: ``{'enable_backup': False}``

A dictionary of settings which can be used to enable optional services provided
by cinder.  Currently only the backup service is available.


``OPENSTACK_NEUTRON_NETWORK``
-----------------------------

.. versionadded:: 2013.1(Grizzly)

Default::

        {
            'enable_router': True,
            'enable_distributed_router': False,
            'enable_ha_router': False,
            'enable_lb': True,
            'enable_quotas': False,
            'enable_firewall': True,
            'enable_vpn': True,
            'profile_support': None,
            'supported_provider_types': ["*"],
            'segmentation_id_range': {}
        }

A dictionary of settings which can be used to enable optional services provided
by Neutron and configure Neutron specific features.  The following options are
available.

``enable_router``:

.. versionadded:: 2014.2(Juno)

Default: ``True``

Enable (True) or disable (False) the panels and menus related
to router and Floating IP features. This option only affects
when Neutron is enabled. If your neutron has no support for
Layer-3 features, or you do no not wish to provide the Layer-3
features through the Dashboard, this should be set to ``False``.

``enable_distributed_router``:

.. versionadded:: 2014.2(Juno)

Default: ``False``

Enable or disable Neutron distributed virtual router (DVR) feature in
the Router panel. For the DVR feature to be enabled, this option needs
to be set to True and your Neutron deployment must support DVR. Even
when your Neutron plugin (like ML2 plugin) supports DVR feature, DVR
feature depends on l3-agent configuration, so deployers should set this
option appropriately depending on your deployment.

``enable_ha_router``:

.. versionadded:: 2014.2(Juno)

Default: ``False``

Enable or disable HA (High Availability) mode in Neutron virtual router
in the Router panel. For the HA router mode to be enabled, this option needs
to be set to True and your Neutron deployment must support HA router mode.
Even when your Neutron plugin (like ML2 plugin) supports HA router mode,
the feature depends on l3-agent configuration, so deployers should set this
option appropriately depending on your deployment.

``enable_lb``:

.. versionadded:: 2013.1(Grizzly)

(Deprecated)

Default: ``True``

Enables the load balancer panel. The load balancer panel will be enabled when
this option is True and your Neutron deployment supports LBaaS. If you want
to disable load balancer panel even when your Neutron supports LBaaS, set it to False.

This option is now marked as "deprecated" and will be removed in Kilo or later release.
The load balancer panel is now enabled only when LBaaS feature is available in Neutron
and this option is no longer needed. We suggest not to use this option to disable the
load balancer panel from now on.

``enable_quotas``:

Default: ``False``

Enable support for Neutron quotas feature. To make this feature work
appropriately, you need to use Neutron plugins with quotas extension support
and quota_driver should be DbQuotaDriver (default config).

``enable_firewall``:

(Deprecated)

Default: ``True``

Enables the firewall panel. firewall panel will be enabled when this
option is True and your Neutron deployment supports FWaaS. If you want
to disable firewall panel even when your Neutron supports FWaaS, set
it to False.

This option is now marked as "deprecated" and will be removed in
Kilo or later release. The firewall panel is now enabled only
when FWaaS feature is available in Neutron and this option is no
longer needed. We suggest not to use this option to disable the
firewall panel from now on.

``enable_vpn``:

(Deprecated)

Default: ``True``

Enables the VPN panel. VPN panel will be enabled when this option is True
and your Neutron deployment supports VPNaaS. If you want to disable
VPN panel even when your Neutron supports VPNaaS, set it to False.

This option is now marked as "deprecated" and will be removed in
Kilo or later release. The VPN panel is now enabled only
when VPNaaS feature is available in Neutron and this option is no
longer needed. We suggest not to use this option to disable the
VPN panel from now on.

``profile_support``:

Default: ``None``

This option specifies a type of network port profile support. Currently the
available value is either ``None`` or ``"cisco"``. ``None`` means to disable
port profile support. ``cisco`` can be used with Neutron Cisco plugins.

``supported_provider_types``:

.. versionadded:: 2014.2(Juno)

Default: ``["*"]``

For use with the provider network extension. Use this to explicitly set which
provider network types are supported. Only the network types in this list will
be available to choose from when creating a network. Network types include
local, flat, vlan, gre, and vxlan. By default all provider network types will
be available to choose from.

Example: ``['local', 'flat', 'gre']``

``segmentation_id_range``:

.. versionadded:: 2014.2(Juno)

Default: ``{}``

For use with the provider network extension. This is a dictionary where each
key is a provider network type and each value is a list containing two numbers.
The first number is the minimum segmentation ID that is valid. The second
number is the maximum segmentation ID. Pertains only to the vlan, gre, and
vxlan network types. By default this option is not provided and each minimum
and maximum value will be the default for the provider network type.

Example: ``{'vlan': [1024, 2048], 'gre': [4094, 65536]}``


``OPENSTACK_SSL_CACERT``
------------------------

.. versionadded:: 2013.2(Havana)

Default: ``None``

When unset or set to ``None`` the default CA certificate on the system is used
for SSL verification.

When set with the path to a custom CA certificate file, this overrides use of
the default system CA certificate. This custom certificate is used to verify all
connections to openstack services when making API calls.


``OPENSTACK_SSL_NO_VERIFY``
---------------------------

.. versionadded:: 2012.2(Folsom)

Default: ``False``

Disable SSL certificate checks in the OpenStack clients (useful for self-signed
certificates).


``POLICY_FILES``
----------------

.. versionadded:: 2013.2(Havana)

Default: ``{'identity': 'keystone_policy.json', 'compute': 'nova_policy.json'}``

This should essentially be the mapping of the contents of ``POLICY_FILES_PATH``
to service types.  When policy.json files are added to ``POLICY_FILES_PATH``,
they should be included here too.


``POLICY_FILES_PATH``
---------------------

.. versionadded:: 2013.2(Havana)

Default:  ``os.path.join(ROOT_PATH, "conf")``

Specifies where service based policy files are located.  These are used to
define the policy rules actions are verified against.

``SESSION_TIMEOUT``
-------------------

.. versionadded:: 2013.2(Havana)

Default: ``"1800"``

Specifies the timespan in seconds inactivity, until a user is considered as
 logged out.

``SAHARA_AUTO_IP_ALLOCATION_ENABLED``
-------------------------------------

Default:  ``False``

This setting notifies the Data Processing (Sahara) system whether or not
automatic IP allocation is enabled.  You would want to set this to True
if you were running Nova Networking with auto_assign_floating_ip = True.


``TROVE_ADD_USER_PERMS`` and ``TROVE_ADD_DATABASE_PERMS``
---------------------------------------------------------

.. versionadded:: 2013.2(Havana)

Default: ``[]``

Trove user and database extension support. By default, support for
creating users and databases on database instances is turned on.
To disable these extensions set the permission to something
unusable such as ``[!]``.

``OPENSTACK_TOKEN_HASH_ALGORITHM``
----------------------------------

.. versionadded:: 2014.2(Juno)

Default: ``"md5"``

The hash algorithm to use for authentication tokens. This must match the hash
algorithm that the identity (Keystone) server and the auth_token middleware
are using. Allowed values are the algorithms supported by Python's hashlib
library.

``OPENSTACK_TOKEN_HASH_ALGORITHM``
----------------------------------

.. versionadded:: 2014.2(Juno)

Default: ``"md5"``

The hash algorithm to use for authentication tokens. This must match the hash
algorithm that the identity (Keystone) server and the auth_token middleware
are using. Allowed values are the algorithms supported by Python's hashlib
library.

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

.. versionadded:: 2013.2(Havana)

Default: ``['localhost']``

This list should contain names (or IP addresses) of the host
running the dashboard; if it's being accessed via name, the
DNS name (and probably short-name) should be added, if it's accessed via
IP address, that should be added. The setting may contain more than one entry.

.. note::

    ALLOWED_HOSTS is required for versions of Django 1.5 and newer.
    If Horizon is running in production (DEBUG is False), set this
    with the list of host/domain names that the application can serve.
    For more information see:
    https://docs.djangoproject.com/en/dev/ref/settings/#allowed-hosts

``DEBUG`` and ``TEMPLATE_DEBUG``
--------------------------------

.. versionadded:: 2011.2(Cactus)

Default: ``True``

Controls whether unhandled exceptions should generate a generic 500 response
or present the user with a pretty-formatted debug information page.

This setting should **always** be set to ``False`` for production deployments
as the debug page can display sensitive information to users and attackers
alike.

``SECRET_KEY``
--------------

.. versionadded:: 2012.1(Essex)

This should absolutely be set to a unique (and secret) value for your
deployment. Unless you are running a load-balancer with multiple Horizon
installations behind it, each Horizon instance should have a unique secret key.

.. note::

    Setting a custom secret key:
    You can either set it to a specific value or you can let Horizon generate a
    default secret key that is unique on this machine, regardless of the
    amount of Python WSGI workers (if used behind Apache+mod_wsgi). However, there
    may be situations where you would want to set this explicitly, e.g. when
    multiple dashboard instances are distributed on different machines (usually
    behind a load-balancer). Either you have to make sure that a session gets all
    requests routed to the same dashboard instance or you set the same SECRET_KEY
    for all of them.


From horizon.utils import secret_key::

    SECRET_KEY = secret_key.generate_or_read_from_file(
    os.path.join(LOCAL_PATH, '.secret_key_store'))

The ``local_settings.py.example`` file includes a quick-and-easy way to
generate a secret key for a single installation.


``SECURE_PROXY_SSL_HEADER``, ``CSRF_COOKIE_SECURE`` and ``SESSION_COOKIE_SECURE``
---------------------------------------------------------------------------------

.. versionadded:: 2013.1(Grizzly)

These three settings should be configured if you are deploying Horizon with
SSL. The values indicated in the default ``local_settings.py.example`` file
are generally safe to use.

When CSRF_COOKIE_SECURE or SESSION_COOKIE_SECURE are set to True, these attributes
help protect the session cookies from cross-site scripting.


.. _pluggable-settings-label:

Pluggable Settings
=================================
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
are added as dependencies on the root Horizon application ``hz``.

``ADD_JS_FILES``
----------------------

.. versionadded:: 2014.2(Juno)

A list of javascript files to be included in the compressed set of files that are
loaded on every page. This is needed for AngularJS modules that are referenced in
``ADD_ANGULAR_MODULES`` and therefore need to be included in every page.

``DISABLED``
------------

.. versionadded:: 2014.1(Icehouse)

If set to ``True``, this settings file will not be added to the settings.

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

The name of the dashboard to be added to ``HORIZON['dashboards']``. Required.

``DEFAULT``
-----------

.. versionadded:: 2014.1(Icehouse)

If set to ``True``, this dashboard will be set as the default dashboard.


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

.. versionadded:: 2014.1(Icehouse)

The following keys are specific to registering or removing a panel:

``PANEL``
---------

.. versionadded:: 2014.1(Icehouse)

The name of the panel to be added to ``HORIZON_CONFIG``. Required.

``PANEL_DASHBOARD``
-------------------

.. versionadded:: 2014.1(Icehouse)

The name of the dashboard the ``PANEL`` associated with. Required.


``PANEL_GROUP``
---------------

.. versionadded:: 2014.1(Icehouse)

The name of the panel group the ``PANEL`` is associated with. If you want the panel to show up
without a panel group, use the panel group "default".

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

To change the default panel of Admin dashboard to Instances panel, create a file
``openstack_dashboard/local/enabled/_80_admin_default_panel.py`` with the
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

The name of the panel group to be added to ``HORIZON_CONFIG``. Required.

``PANEL_GROUP_NAME``
--------------------

.. versionadded:: 2014.1(Icehouse)

The display name of the PANEL_GROUP. Required.

``PANEL_GROUP_DASHBOARD``
-------------------------

.. versionadded:: 2014.1(Icehouse)

The name of the dashboard the ``PANEL_GROUP`` associated with. Required.



Examples
--------

To add a new panel group to the Admin dashboard, create a file
``openstack_dashboard/local/enabled/_90_admin_add_panel_group.py`` with the
following content::

    PANEL_GROUP = 'plugin_panel_group'
    PANEL_GROUP_NAME = 'Plugin Panel Group'
    PANEL_GROUP_DASHBOARD = 'admin'

