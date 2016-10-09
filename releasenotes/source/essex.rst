==========================
Essex Series Release Notes
==========================

Release Overview
================

During the Essex release cycle, Horizon underwent a significant set of internal
changes to allow extensibility and customization while also adding a significant
number of new features and bringing much greater stability to every interaction
with the underlying components.

Highlights
==========

Extensibility
-------------

Making Horizon extensible for third-party developers was one of the core
goals for the Essex release cycle. Massive strides have been made to allow
for the addition of new "plug-in" components and customization of OpenStack
Dashboard deployments.

To support this extensibility, all the components used to build on Horizon's
interface are now modular and reusable. Horizon's own dashboards use these
components, and they have all been built with third-party developers in mind.
Some of the main components are listed below.

Dashboards and Panels
~~~~~~~~~~~~~~~~~~~~~

Horizon's structure has been divided into logical groupings called dashboards
and panels. Horizon's classes representing these concepts handle all the
structural concerns associated with building a complete user interface
(navigation, access control, url structure, etc.).

Data Tables
~~~~~~~~~~~

One of the most common activities in a dashboard user interface is simply
displaying a list of resources or data and allowing the user to take actions on
that data. To this end, Horizon abstracted the commonalities of this task into a
reusable set of classes which allow developers to programmatically create
displays and interactions for their data with minimal effort and zero
boilerplate.

Tabs and TabGroups
~~~~~~~~~~~~~~~~~~

Another extremely common user-interface element is the use of "tabs" to break
down discrete groups of data into manageable chunks. Since these tabs often
encompass vastly different data, may have completely different access
restrictions, and may sometimes be better-off being loaded dynamically rather
than with the initial page load, Horizon includes tab and tab group classes for
constructing these interfaces elegantly and with no knowledge of the HTML, CSS
or JavaScript involved.

Nova Features
-------------

Support for Nova's features has been greatly improved in Essex:

* Support for Nova volumes, including:

  * Volumes creation and management.
  * Volume snapshots.
  * Realtime AJAX updating for volumes in transition states.

* Improved Nova instance display and interactions, including:

  * Launching instances from volumes.
  * Pausing/suspending instances.
  * Displaying instance power states.
  * Realtime AJAX updating for instances in transition states.

* Support for managing Floating IP address pools.
* New instance and volume detail views.

Settings
--------

A new "Settings" area was added that offers several useful functions:

* EC2 credentials download.
* OpenStack RC file download.
* User language preference customization.

User Experience Improvements
----------------------------

* Support for batch actions on multiple resources (e.g. terminating multiple
  instances at once).
* Modal interactions throughout the entire UI.
* AJAX form submission for in-place validation.
* Improved in-context help for forms (tooltips and validation messages).


Community
---------

* Creation and publication of a set of Human Interface Guidelines (HIG).
* Copious amounts of documentation for developers.

Under The Hood
--------------

* Internationalization fully enabled, with all strings marked for translation.
* Client library changes:

  * Full migration to python-novaclient from the deprecated openstackx library.
  * Migration to python-keystoneclient from the deprecated keystone portion
    of the python-novaclient library.

* Client-side templating capabilities for more easily creating dynamic
  interactions.
* Frontend overhaul to use the Bootstrap CSS/JS framework.
* Centralized error handling for vastly improved stability/reliability
  across APIs/clients.
* Completely revamped test suite with comprehensive test data.
* Forward-compatibility with Django 1.4 and the option of cookie-based sessions.

Known Issues and Limitations
============================

Quantum
-------

Quantum support has been removed from Horizon for the Essex release. It will be
restored in Folsom in conjunction with Quantum's first release as a core
OpenStack project.

Keystone
--------

Due to the mechanisms by which Keystone determines "admin"-ness for a user, an
admin user interacting with the "Project" dashboard may see some inconsistent
behavior such as all resources being listed instead of only those belonging to
that project, or only being able to return to the "Admin" dashboard while
accessing certain projects.

Exceptions during customization
-------------------------------

Exceptions raised while overriding built-in Horizon behavior via the
"customization_module" setting may trigger a bug in the error handling
which will mask the original exception.

Backwards Compatibility
=======================

The Essex Horizon release is only partially backwards-compatible with Diablo
OpenStack components. While it is largely possible to log in and interact, many
functions in Nova, Glance and Keystone changed too substantially in Essex to
maintain full compatibility.
