===========================
Folsom Series Release Notes
===========================

Release Overview
================

The Folsom release cycle brought several major advances to Horizon's user
experience while also reintroducing Quantum networking as a core piece
of the OpenStack Dashboard.

Highlights
==========

Networking (Quantum)
--------------------

With Quantum being a core project for the Folsom release, we worked closely
with the Quantum team to bring networking support back into Horizon. This
appears in two primary places: the Networks panel in both the Project and
Admin dashboards, and the Network tab in the Launch Instance workflow. Expect
further improvements in these areas as Quantum continues to mature and more
users adopt this model of virtual network management.

User Experience
---------------

Workflows
~~~~~~~~~

By far the biggest UI/UX change in the Folsom release is the introduction of
programmatic workflows. These components allow developers to create concise
interactions that combine discrete tasks spanning multiple services and
resources in a user-friendly way and with minimal boilerplate code. Within
a workflow, related objects can also be dynamically created so users don't lose
their place when they realize the item they wanted isn't currently available.
Look for examples of these workflows in Launch Instance, Associate Floating IP,
and Create/Edit Project.

Resource Browser
~~~~~~~~~~~~~~~~

Another cool new component is an interface designed for "browsing" resources
which are nested under a parent resource. The object store (Swift) is a prime
example of this. Now there is a consistent top-level navigation for containers
on the left-hand pane of the "browser" while the right-hand pane lets you
explore within those containers and sub-folders.

User Experience Improvements
----------------------------

* Timezone support is now enabled. You can select your preferred timezone
  in the User Settings panel.

Community
---------

* Third-party developers who wish to build on Horizon can get started much
  faster using the new dashboard and panel templates. See the docs on
  `creating a dashboard`_ and `creating a panel`_ for more information.

* A `thorough set of documentation`_ for developers on how to go about
  internationalizing, localizing and translating OpenStack projects
  is now available.

.. _creating a dashboard: https://docs.openstack.org/horizon/latest/contributor/tutorials/dashboard.html#creating-a-dashboard
.. _creating a panel: https://docs.openstack.org/horizon/latest/contributor/tutorials/dashboard.html#creating-a-panel
.. _thorough set of documentation: https://wiki.openstack.org/Translations

Under The Hood
--------------

* The python-swiftclient library and python-cinderclient libraries are now
  used under the hood instead of cloudfiles and python-novaclient respectively.

* Internationalization of client-side JavaScript is now possible in addition
  to server-side Python code.

* Keystone authentication is now handled by a proper pluggable Django
  authentication backend, offering significantly better and more reliable
  security for Horizon.

Other Improvements and Fixes
----------------------------

Some of the general areas of improvement include:

* Images can now be added to Glance by providing a URL for Glance to download
  the image data from.

* Quotas are now displayed dynamically throughout the Project dashboard.

* API endpoints are now displayed on the OpenStack RC File panel so they
  can be organically discovered by an end-user.

* DataTables now support a summation row at the bottom of the table.

* Better cross-browser support (Safari and IE particularly).

* Fewer API calls to OpenStack endpoints (improves performance).

* Better validation of what actions are permitted when.

* Improved error handling and error messages.

Known Issues and Limitations
============================

Floating IPs and Quantum
------------------------

Due to the very late addition of floating IP support in Quantum, Nova's
integration there is lacking, so floating IP-related API calls to Nova will
fail when your OpenStack deployment uses Quantum for networking. This means
that Horizon actions such as "allocate" and "associate" floating IPs will
not work either since they rely on the underlying APIs.

Pagination
----------

A number of the "index" pages don't fully work with API pagination yet,
causing them to only display the first chunk of results returned by the API.
This number is often 1000 (as in the case of novaclient results), but does vary
somewhat.

Deleting large numbers of resources simultaneously
--------------------------------------------------

Using the "select all" checkbox to delete large numbers of resources via the
API can cause network timeouts (depending on configuration). This is
due to the APIs not supporting bulk-deletion natively, and consequently Horizon
has to send requests to delete each resource individually behind the scenes.

Backwards Compatibility
=======================

The Folsom Horizon release should be fully-compatible with both Folsom and
Essex versions of the rest of the OpenStack core projects (Nova, Swift, etc.).
While some features work significantly better with an all-Folsom stack due
to bugfixes, etc. in underlying services, there should not be any limitations
on what will or will not function. (Note: Quantum was not a core OpenStack
project in Essex, and thus this statement does not apply to network management.)

In terms of APIs provided for extending Horizon, there are a handful of
backwards-incompatible changes that were made:

* The ``can_haz`` and ``can_haz_list`` template filters have been renamed
  to ``has_permissions`` and ``has_permissions_on_list`` respectively.

* The dashboard-specific ``base.html`` templates (e.g. ``nova/base.html``,
  ``syspanel/base.html``, etc.) have been removed in favor of a single
  ``base.html`` template.

* In conjunction with the previous item, the dashboard-specific template blocks
  (e.g. ``nova_main``, ``syspanel_main``, etc.) have been removed in favor of
  a single ``main`` template block.

Overall, though, great effort has been made to maintain compatibility for
third-party developers who may have built on Horizon so far.
