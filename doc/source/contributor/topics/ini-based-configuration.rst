=================================
Defining default settings in code
=================================

.. note::

   This page tries to explain the plan to define default values
   of horizon/openstack_dashboard settings in code.
   This includes a blueprint
   `ini-based-configuration
   <https://blueprints.launchpad.net/horizon/+spec/ini-based-configuration>`__.
   This page will be updated once the effort is completed.

Planned Steps
=============

1. Define the default values of existing settings
2. Revisit HORIZON_CONFIG
3. Introduce ``oslo.config``

Define default values of existing settings
==========================================

Currently all default values are defined in codes where they are consumed.
This leads to the situation that it is not easy to know what are the default
values and in a worse case default values defined in our codebase can have
different default values.

As the first step toward ini-based-configuration, I propose to define
all default values of existing settings in a single place per module.
More specifically, the following modules are used:

- ``openstack_dashboard.defaults`` for openstack_dashboard
- ``horizon.defaults`` for horizon
- ``openstack_auth.defaults`` for openstack_auth

``horizon.defaults`` load ``openstack_auth.defaults`` and overrides
openstack_auth settings if necessary.
Similarly, ``openstack_dashboard.defaults`` loads ``horizon.defaults`` and
overrides horizon (and openstack_auth) settings if necessary.

The current style of ``getattr(settings, <foo>, <default value>)`` will be
removed at the same time.

Note that ``HORIZON_CONFIG`` is not touched in this step. It will be covered in
the next step.

Handling Django settings
------------------------

Django provides a lot of settings and it is not practical to cover
all in horizon. Only Django settings which horizon explicitly set
will be defined in a dedicated python module.

The open question is how to maintain Django related settings
in openstack_dashboard and horizon. How can we make them common?
The following files are related:

- openstack_dashboard.settings (and local_settings.py)
- openstack_dashboard.test.settings
- horizon.test.settings

This will be considered as the final step of the ini-based-configuration effort
after horizon and openstack_dashboard settings succeed to be migrated to
oslo.config explained below.

Revisit HORIZON_CONFIG
======================

HORIZON_CONFIG is an internal interface now and most/some(?) of them should not
be exposed as config options. For example, the horizon plugin mechanism touches
HORIZON_CONFIG to register horizon plugins.

It is better to expose only HORIZON_CONFIG settings which can be really exposed
to operators. For such settings, we should define new settings in
openstack_dashboard and can populate them into HORIZON_CONFIG in
``settings.py``.

For example, ``ajax_poll_interval`` in HORIZON_CONFIG can be
exposed to operators. In such case, we can define a new settings
``AJAX_POLL_INTERVAL`` in ``openstack_dashboard/defaults.py``
(or ``horizon/defaults.py``).

Investigation is being summarized in
`an etherpad page <https://etherpad.openstack.org/p/horizon-config-rethink>`__.

Introduce oslo.config
=====================

local_settings.py will have a priority over oslo.config. This means settings
values from oslo.config will be loaded first and then ``local_settings.py`` and
``local_settings.d`` will be loaded in ``settings.py``.

Basic strategy of mapping
-------------------------

* The current naming convention is random, so it sounds less reasonable to use
  the same name for oslo.config. oslo.config and python ini-based configuration
  mechanism provide a concept of category and there is no reason to use it.
  As category name, the categories of
  :doc:`/configuration/settings`
  (like keystone, glance) will be honored.

  For example, some keystone settings have a prefix ``OPENSTACK_KEYSTONE_`` like
  OPENSTACK_KEYSTONE_DEFAULT_ROLE.
  Some use ``KEYSTONE_`` like ``KEYSTONE_IDP_PROVIDER_ID``. Some do not (like
  ``ENFORCE_PASSWORD_CHECK``). In the oslo.config options, all prefixes will be
  dropped. The mapping will be:

  * ``OPENSTACK_KEYSTONE_DEFAULT_ROLE`` <-> ``[keystone] default_role``
  * ``KEYSTONE_IDP_PROVIDER_ID`` <-> ``[keystone] idp_provider_id``
  * ``ENFORCE_PASSWORD_CHECK`` <-> ``[keystone] enforce_password_check``

* ``[default]`` section is not used as much as possible. It will be used only
  for limited number of well-known options. Perhaps some common Django settings
  like ``DEBUG``, ``LOGGING`` will match this category.

* Opt classes defined in oslo.config are used as much as possible.

  * StrOpt, IntOpt
  * ListOpt
  * MultiStrOpt
  * DictOpt

* A dictionary settings will be broken down into separate options.
  Good examples are ``OPENSTACK_KEYSTONE_BACKEND`` and
  ``OPENSTACK_NEUTRON_NETWORK``.

  * ``OPENSTACK_KEYSTONE_BACKEND['name']`` <-> ``[keystone] backend_name``
  * ``OPENSTACK_KEYSTONE_BACKEND['can_edit_user']`` <->
    ``[keystone] backend_can_edit_user``
  * ``OPENSTACK_KEYSTONE_BACKEND['can_edit_group']`` <->
    ``[keystone] backend_can_edit_group``
  * ``OPENSTACK_NEUTRON_NETWORK['enable_router']`` <->
    ``[neutron] enable_router``
  * ``OPENSTACK_NEUTRON_NETWORK['enable_ipv6']`` <->
    ``[neutron] enable_ipv6``

Automatic Mapping
-----------------

The straight-forward approach is to have a dictionary from setting names to
oslo.config options like:

.. code-block:: python

   {
     'OPENSTACK_KEYSTONE_DEFAULT_ROLE': ('keystone', 'default_role'),
     'OPENSTACK_NEUTRON_NETWORK': {
        'enable_router': ('neutron', 'enable_router'),
        'enable_ipv6': ('neutron', 'enable_ipv6'),
     ...
   }

A key of the top-level dict is a name of Django settings.
A corresponding value specifies oslo.config name by a list or a tuple where the
first and second elements specify a section and a option name respectively.

When a value is a dict, this means a corresponding Django dict setting is
broken down into several oslo.config options. In the above example,
``OPENSTACK_NEUTRON_NETWORK['enable_router']`` is mapped to
``[neutron] enable_router``.

Another idea is to introduce a new field to oslo.config classes.
oslo-sample-generator might need to be updated. If this approach is really
attractive, we can try this approach in future. The above dictionary-based
approach will be used in the initial effort.

.. code-block:: python

   cfg.StrOpt(
     'default_role',
     default='_member_',
     django-setting='OPENSTACK_KEYSTONE_DEFAULT_ROLE',
     help=...
   )

   cfg.BoolOpt(
     'enable_router',
     default=True,
     django_setting=('OPENSTACK_NEUTRON_NETWORK', 'enable_router'),
     help=....)
   )

Special Considerations
----------------------

LOGGING
~~~~~~~

``LOGGING`` setting is long enough. Python now recommend to configure logging
using python dict directly, but from operator/packager perspective the legacy
style of using the ini format sounds reasonable. The ini format is also used in
other OpenStack projects too. In this effort, I propose to use the logging
configuration via the ini format file and specify the logging conf file in a
oslo.config option

Adopting oslo.log might be a good candidate, but it is not covered by this
effort. It can be explored as future possible improvement.

SECURITY_GROUP_RULES
~~~~~~~~~~~~~~~~~~~~

``SECURITY_GROUP_RULES`` will be defined by YAML file.
The YAML file can be validated by JSON schema in future
(out of the scope of this effort)

``all_tcp``, ``all_udp`` and ``all_icmp`` are the reserved keyword, so it looks
better to split the first three rules (``all_tcp`` to ``all_icmp``) and other
remaining rules. The remaining rules will be loaded from a YAML file. For the
first three rules, a boolean option to control their visibility in the security
group rule form will be introduces in oslo.config. I am not sure this option is
required or not, but as the first step of the migration it is reasonable to
provide all compatibilities.

Handling Django settings
~~~~~~~~~~~~~~~~~~~~~~~~

Django (and django related packages) provide many settings.
It is not a good idea to expose all of them via oslo.config.
What should we expose?

The proposal here is to expose only settings which openstack_dashboard expects
to expose to deployers. Most Django settings are internally used in
``openstack_dashboard/settings.py``. Settings required for horizon plugins
are already exposed via the plugin settings, so there is no need to expose
them. If deployers would like to customize Django basic settings, they can
still configure them via ``local_settings.py`` or ``local_settings.d``.
