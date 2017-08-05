=============================
Icehouse Series Release Notes
=============================

Release Overview
================

The Icehouse release cycle brings several improvements to Horizon's
user experience, improved extensibility, and support for many
additional features in existing projects. The community continues to
grow. Read more for the specifics.

Highlights
==========

New Features
------------

Nova
~~~~

The number of OpenStack Compute (Nova) features that are supported in Icehouse
grew. New features in the Icehouse release include:

* Live Migration Support
* HyperV Console Support
* Disk config extension support
* Improved support for managing host aggregates and availability zones
* Support for easily setting flavor extra specs

Cinder
~~~~~~

In an ongoing effort to implement Role Based Access Support throughout Horizon,
access controls were added in the OpenStack Volume (Cinder) related panels.
Utilization of the Cinder v2 API is now a supported option in the Icehouse
release. The ability to extend volumes is now available as well.

Neutron
~~~~~~~

Display of Router Rules for routers where they are defined is now supported in
Horizon.

Swift
~~~~~

With Icehouse, the ability for users to create containers and mark them as
public is now available. Links are added to download these public containers.
Users can now explicitly create pseudo directories rather than being required to
create them as part of the container creation process.

Heat
~~~~

In Icehouse, Horizon delivers support for updating existing Heat stacks.
Now stacks that have already been deployed can be adjusted and redeployed. The
updated template is also validated when updated. Additionally, support for
adding environment files was included.

Ceilometer
~~~~~~~~~~

Horizon has added support for administrators to query Ceilometer and
view a daily usage report per project across services through the
OpenStack Dashboard to better understand how system resources are being
consumed by individual projects.

Trove Databases
~~~~~~~~~~~~~~~

The OpenStack Database as a Service project (Trove) is part of the
integrated release in the Icehouse cycle.  Improvements to the client
connections and overall stability were added in the Icehouse cycle.


User Experience Improvements
----------------------------

Extensible Enhancements
~~~~~~~~~~~~~~~~~~~~~~~

The primary dashboard and panel navigation has been updated from the tab
navigation to an accordion implementation. Dashboards and Panel Groups are now
expandable and collapsible in the page navigation. This change allows for the
addition of more dashboards as well as accommodates the increasing number of
panels in dashboards.

Wizard
~~~~~~

Horizon now provides a Wizard control to complete multi-step interdependent
tasks. This is now utilized in the create network action.

Inline Table Editing
~~~~~~~~~~~~~~~~~~~~

Tables can now be written to support editing fields in the table to reduce the
need for opening separate forms. The first sample of this is in the Admin
dashboard, Projects panel.

Self-Service Password Change
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Leveraging enhancements to Identity API v3 (Keystone), users can now change
their own passwords without the need to involve an administrator. This
functionality was previously only available with Identity API v2.0.

Server Side Table Filtering
~~~~~~~~~~~~~~~~~~~~~~~~~~~

Tables can now easily be wired to filter results from underlying API calls
based on criteria selected by the user rather than just perform an on page
search. The first example of this is in the Admin dashboard, Instances panel.

Under The Hood
--------------

JavaScript
~~~~~~~~~~

In a move to provide a better user experience, Horizon has adopted AngularJS as
the primary JavaScript framework. JavaScript is now a browser requirement to
run the Horizon interface. More to come in Juno.

Plugin Architecture
~~~~~~~~~~~~~~~~~~~

Horizon now boasts dynamic loading/disabling of dashboards, panel groups and
panels. By merely adding a file in the ``enabled`` directory, the selection of
items loaded into Horizon can be altered. Editing the Django settings file is
no longer required.

For more information see
`Pluggable Settings <https://docs.openstack.org/horizon/latest/configuration/pluggable_panels.html>`__.

Integration Test Framework
~~~~~~~~~~~~~~~~~~~~~~~~~~

Horizon now supports running integration tests against a working devstack
system. There is a limited test suite, but this a great step forward and allows
full integration testing.

Django 1.6 Support
~~~~~~~~~~~~~~~~~~

Django versions 1.4 - 1.6 are now supported by Horizon.


Upgrade Information
===================

Beginning with the Icehouse cycle, there is now a requirement for JavaScript
support in browsers used with OpenStack Dashboard.

Page Layout Changes
-------------------

The overall structure of the page layout in Horizon has been altered. Existing
templates by 3rd parties to override page templates may require some rework.

Default Hypervisor Settings Changes
-----------------------------------

The default for ``can_set_password`` is now ``False``. This means that unless
the setting is explicitly set to ``True``, the option to set an
'Admin password' for an instance will not be shown in the Launch Instance
workflow. Not all hypervisors support this feature which created confusion with
users.

The default for ``can_set_mountpoint`` is now ``False``, and should be set to
``True`` in the settings in order to add the option to set the mount point for
volumes in the dashboard. At this point only the Xen hypervisor supports this
feature.

To change the behavior around hypervisor management in Horizon you must add the
``OPENSTACK_HYPERVISOR_FEATURES`` setting to your ``settings.py`` or
``local_settings.py`` file.

For more information see
`OPENSTACK_HYPERVISOR_FEATURES setting <https://docs.openstack.org/horizon/latest/configuration/settings.html#openstack-hypervisor-features>`__.

Known Issues and Limitations
============================

Multi-Domain Cross Service Support
----------------------------------

While Horizon supports managing Identity v3 entities and authenticating in a
multi-domain Keystone configuration, there is a v3, v2.0 token compatibility
issue when trying to manage resources for users outside the ``default``
domain. For this reason, v2.0 has been restored as the default API version
for OpenStack Identity (Keystone). For a single domain environment, Keystone
v3 API can still be used via the ``OPENSTACK_API_VERSION`` setting.
