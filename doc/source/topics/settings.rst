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
    enabled in the OpenStack Dashboard. This code has beenlong-since removed and
    those pre-Essex settings have no impact now.

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

``dashboards``
--------------

Default: ``None``

A list containing the slugs of any dashboards which should be active in this
Horizon installation. The dashboards listed must be in a Python module which
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

Default: None

If provided, a "Help" link will be displayed in the site header which links
to the value of this settings (ideally a URL containing help information).

``exceptions``
--------------

Default: ``{'unauthorized': [], 'not_found': [], 'recoverable': []}``

A dictionary containing classes of exceptions which Horizon's centralized
exception handling should be aware of.

``password_validator``
----------------------

Default: {'regex': '.*', 'help_text': _("Password is not accepted")}

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


OpenStack Settings (Partial)
============================

The following settings inform the OpenStack Dashboard of information about the
other OpenStack projects which are part of this cloud and control the behavior
of specific dashboards, panels, API calls, etc.

``OPENSTACK_HOST``
------------------

Default: ``"127.0.0.1"``

The hostname of the Keystone server used for authentication if you only have
one region. This is often the *only* settings that needs to be set for a
basic deployment.


``OPENSTACK_KEYSTONE_URL``
--------------------------

Default: ``"http://%s:5000/v2.0" % OPENSTACK_HOST``

The full URL for the Keystone endpoint used for authentication. Unless you
are using HTTPS, running your Keystone server on a nonstandard port, or using
a nonstandard URL scheme you shouldn't need to touch this setting.

``AVAILABLE_REGIONS``
---------------------

Default: ``None``

A tuple of tuples which define multiple regions. The tuple format is
``('http://{{keystone_host}}:5000/v2.0', '{{region_name}}')``. If any regions
are specified the login form will have a dropdown selector for authenticating
to the appropriate region, and there will be a region switcher dropdown in
the site header when logged in.

If you do not have multiple regions you should use the ``OPENSTACK_HOST`` and
``OPENSTACK_KEYSTONE_URL`` settings above instead.

``OPENSTACK_KEYSTONE_DEFAULT_ROLE``
-----------------------------------

Default: "Member"

The name of the role which will be assigned to a user when added to a project.
This name must correspond to a role name in Keystone.

``OPENSTACK_SSL_NO_VERIFY``
---------------------------

Default: ``False``

Disable SSL certificate checks in the OpenStack clients (useful for self-signed
certificates).

``OPENSTACK_KEYSTONE_BACKEND``
------------------------------

Default: ``{'name': 'native', 'can_edit_user': True, 'can_edit_project': True}``

A dictionary containing settings which can be used to identify the
capabilities of the auth backend for Keystone.

If Keystone has been configured to use LDAP as the auth backend then set
``can_edit_user`` and ``can_edit_project`` to ``False`` and name to ``"ldap"``.


``OPENSTACK_HYPERVISOR_FEATURES``
---------------------------------

Default: ``{'can_set_mount_point': True, 'can_encrypt_volumes': False}``

A dictionary containing settings which can be used to identify the
capabilities of the hypervisor for Nova.

Some hypervisors have the ability to set the mount point for volumes attached
to instances (KVM does not). Setting ``can_set_mount_point`` to ``False`` will
remove the option to set the mount point from the UI.

In the Havana release, there will be a feature for encrypted volumes
which will be controlled by the ``can_encrypt_volumes``. Setting it to ``True``
in the Grizzly release will have no effect.

``OPENSTACK_NEUTRON_NETWORK``
-----------------------------

Default: ``{'enable_lb': False}``

A dictionary of settings which can be used to enable optional services provided
by neutron.  Currently only the load balancer service is available.

``OPENSTACK_ENDPOINT_TYPE``
---------------------------

Default: ``"internalURL"``

A string which specifies the endpoint type to use for the endpoints in the
Keystone service catalog. If Horizon is running external to the OpenStack
environment you may wish to use ``"publicURL"`` instead.

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

``POLICY_FILES_PATH``
---------------------

Default:  ``os.path.join(ROOT_PATH, "conf")``

Specifies where service based policy files are located.  These are used to
define the policy rules actions are verified against.

``POLICY_FILES``
----------------

Default: ``{ 'identity': 'keystone_policy.json', 'compute': 'nova_policy.json'}``

This should essentially be the mapping of the contents of ``POLICY_FILES_PATH``
to service types.  When policy.json files are added to ``POLICY_FILES_PATH``,
they should be included here too.

``OPENSTACK_IMAGE_BACKEND``
---------------------------

Default: ``{ 'image_formats': [('', ''), ('aki', _('AKI - Amazon Kernel Image')),
('ami', _('AMI - Amazon Machine Image')), ('ari', _('ARI - Amazon Ramdisk Image')),
('iso', _('ISO - Optical Disk Image')), ('qcow2', _('QCOW2 - QEMU Emulator')),
('raw', _('Raw')), ('vdi', _('VDI')), ('vhd', _('VHD')), ('vmdk', _('VMDK'))] }``

Used to customize features related to the image service, such as the list of
supported image formats.

Django Settings (Partial)
=========================

.. warning::

    This is not meant to be anywhere near a complete list of settings for
    Django. You should always consult the upstream documentation, especially
    with regards to deployment considerations and security best-practices.

There are a few key settings you should be aware of for development and the
most basic of deployments. Further recommendations can be found in the
Deploying Horizon section of this documentation.

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
