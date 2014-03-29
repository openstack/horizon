==================
Horizon Quickstart
==================

..  Note ::

    This section has been tested for Horizon on Ubuntu (12.04-64) and Fedora-based (RHEL 6.4) distributions. Feel free to add notes and any changes according to your experiences or operating system.

Linux Systems
=============

Install the prerequisite packages.

On Ubuntu::

    > sudo apt-get install git python-dev python-virtualenv libssl-dev libffi-dev

On Fedora-based distributions (e.g., Fedora/RHEL/CentOS/Scientific Linux)::

    > sudo yum install gcc git-core python-devel python-virtualenv openssl-devel libffi-devel

Setup
=====

To setup a Horizon development environment simply clone the Horizon git
repository from http://github.com/openstack/horizon and execute the
``run_tests.sh`` script from the root folder (see :doc:`ref/run_tests`)::

    > git clone https://github.com/openstack/horizon.git
    > cd horizon
    > ./run_tests.sh

Next you will need to setup your Django application config by copying ``openstack_dashboard/local/local_settings.py.example`` to ``openstack_dashboard/local/local_settings.py``. To do this quickly you can use the following command::

    > cp openstack_dashboard/local/local_settings.py.example openstack_dashboard/local/local_settings.py

Horizon assumes a single end-point for OpenStack services which defaults to
the local host (127.0.0.1). If this is not the case change the
``OPENSTACK_HOST`` setting in the ``openstack_dashboard/local/local_settings.py`` file, to the actual IP address of the OpenStack end-point Horizon should use.

To start the Horizon development server use the Django ``manage.py`` utility
with the context of the virtual environment::

    > tools/with_venv.sh ./manage.py runserver

Alternately specify the listen IP and port::

    > tools/with_venv.sh ./manage.py runserver 0.0.0.0:8080

.. note::

    If you would like to run commands without the prefix of ``tools/with_venv.sh`` you may source your environment directly. This will remain active as long as your shell session stays open::

    > source .venv/bin/activate


Once the Horizon server is running point a web browser to http://localhost:8000
or to the IP and port the server is listening for.

.. note::

    The ``DevStack`` project (http://devstack.org/) can be used to install
    an OpenStack development environment from scratch.

.. note::

    The minimum required set of OpenStack services running includes the
    following:

    * Nova (compute, api, scheduler, and network)
    * Glance
    * Keystone

    Optional support is provided for Swift.

Horizon's Structure
===================

This project is a bit different from other OpenStack projects in that it has
two very distinct components underneath it: ``horizon``, and
``openstack_dashboard``.

The ``horizon`` directory holds the generic libraries and components that can
be used in any Django project.

The ``openstack_dashboard`` directory contains a reference Django project that
uses ``horizon``.

For development, both pieces share an environment which (by default) is
built with the ``tools/install_venv.py`` script. That script creates a
virtualenv and installs all the necessary packages.

If dependencies are added to either ``horizon`` or ``openstack_dashboard``,
they should be added to ``requirements.txt``.

  .. important::

    If you do anything which changes the environment (adding new dependencies
    or renaming directories are both great examples) be sure to increment the
    ``environment_version`` counter in :doc:`run_tests.sh <ref/run_tests>`.

Project
=======

Dashboard configuration
-----------------------

To add a new dashboard to your project, you need to add a configuration file to
``openstack_dashboard/local/enabled`` directory. For more information on this,
see :ref:`pluggable-settings-label`.

There is also an alternative way to add a new dashboard, by adding it to
Django's ``INSTALLED_APPS`` setting. For more information about this, see
:ref:`dashboards`. However, please note that the recommended way is to take
advantage of the pluggable settings feature.

URLs
----

Then you add a single line to your project's ``urls.py``::

    url(r'', include(horizon.urls)),

Those urls are automatically constructed based on the registered Horizon apps.
If a different URL structure is desired it can be constructed by hand.

Templates
---------

Pre-built template tags generate navigation. In your ``nav.html``
template you might have the following::

    {% load horizon %}

    <div class='nav'>
        {% horizon_main_nav %}
    </div>

And in your ``sidebar.html`` you might have::

    {% load horizon %}

    <div class='sidebar'>
        {% horizon_dashboard_nav %}
    </div>

These template tags are aware of the current "active" dashboard and panel
via template context variables and will render accordingly.

Application
===========

Structure
---------

An application would have the following structure (we'll use project as
an example)::

    project/
    |---__init__.py
    |---dashboard.py <-----Registers the app with Horizon and sets dashboard properties
    |---overview/
    |---images/
        |-- images
        |-- __init__.py
        |---panel.py <-----Registers the panel in the app and defines panel properties
        |-- snapshots/
        |-- templates/
        |-- tests.py
        |-- urls.py
        |-- views.py
        ...
    ...

Dashboard Classes
-----------------

Inside of ``dashboard.py`` you would have a class definition and the registration
process::

    import horizon

    ....
    # ObjectStorePanels is an example for a PanelGroup
    # for panel classes in general, see below
    class ObjectStorePanels(horizon.PanelGroup):
        slug = "object_store"
        name = _("Object Store")
        panels = ('containers',)


    class Project(horizon.Dashboard):
        name = _("Project") # Appears in navigation
        slug = "project"    # Appears in URL
        # panels may be strings or refer to classes, such as
        # ObjectStorePanels
        panels = (BasePanels, NetworkPanels, ObjectStorePanels)
        default_panel = 'overview'
        supports_tenants = True
        ...

    horizon.register(Project)

Panel Classes
-------------

To connect a :class:`~horizon.Panel` with a :class:`~horizon.Dashboard` class
you register it in a ``panel.py`` file like so::

    import horizon

    from openstack_dashboard.dashboards.project import dashboard


    class Images(horizon.Panel):
        name = "Images"
        slug = 'images'
        permissions = ('openstack.roles.admin', 'my.other.permission',)


    # You could also register your panel with another application's dashboard
    dashboard.Project.register(Images)

By default a :class:`~horizon.Panel` class looks for a ``urls.py`` file in the
same directory as ``panel.py`` to include in the rollup of url patterns from
panels to dashboards to Horizon, resulting in a wholly extensible, configurable
URL structure.
