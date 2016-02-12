==========
Quickstart
==========

..  Note ::

    This section has been tested for Horizon on Ubuntu (12.04-64) and RPM-based (RHEL 7.x) distributions. Feel free to add notes and any changes according to your experiences or operating system.

Linux Systems
=============

Install the prerequisite packages.

On Ubuntu::

    > sudo apt-get install git python-dev python-virtualenv libssl-dev libffi-dev

On RPM-based distributions (e.g., Fedora/RHEL/CentOS/Scientific Linux)::

    > sudo yum install gcc git-core python-devel python-virtualenv openssl-devel libffi-devel which

Setup
=====

To setup a Horizon development environment simply clone the Horizon git
repository from http://github.com/openstack/horizon and execute the
``run_tests.sh`` script from the root folder (see :doc:`ref/run_tests`)::

    > git clone https://github.com/openstack/horizon.git
    > cd horizon
    > ./run_tests.sh

.. note::

    Running ``run_tests.sh`` will build a virtualenv, ``.venv``, where all the
    python dependencies for Horizon are installed and referenced. After the
    dependencies are installed, the unit test suites in the Horizon repo will be
    executed.  There should be no errors from the tests.

Next you will need to setup your Django application config by copying ``openstack_dashboard/local/local_settings.py.example`` to ``openstack_dashboard/local/local_settings.py``. To do this quickly you can use the following command::

    > cp openstack_dashboard/local/local_settings.py.example openstack_dashboard/local/local_settings.py

.. note::

    To add new settings or customize existing settings, modify the ``local_settings.py`` file.

Horizon assumes a single end-point for OpenStack services which defaults to
the local host (127.0.0.1), as is the default in DevStack. If this is not the
case change the ``OPENSTACK_HOST`` setting in the
``openstack_dashboard/local/local_settings.py`` file, to the actual IP address
of the OpenStack end-point Horizon should use.

You can save changes you made to
``openstack_dashboard/local/local_settings.py`` with the following command::

    > python manage.py migrate_settings --gendiff

.. note::

    This creates a ``local_settings.diff`` file which is a diff between
    ``local_settings.py`` and ``local_settings.py.example``

If you upgrade Horizon, you might need to update your
``openstack_dashboard/local/local_settings.py`` file with new parameters from
``openstack_dashboard/local/local_settings.py.example`` to do so, first update
Horizon::

    > git remote update && git pull --ff-only origin master

Then update your  ``openstack_dashboard/local/local_settings.py`` file::

    > mv openstack_dashboard/local/local_settings.py openstack_dashboard/local/local_settings.py.old
    > python manage.py migrate_settings

.. note::

    This applies ``openstack_dashboard/local/local_settings.diff`` on
    ``openstack_dashboard/local/local_settings.py.example`` to regenerate an
    ``openstack_dashboard/local/local_settings.py`` file.
    The migration can sometimes have difficulties to migrate some settings, if
    this happens you will be warned with a conflict message pointing to an
    ``openstack_dashboard/local/local_settings.py_Some_DateTime.rej`` file.
    In this file, you will see the lines which could not be automatically
    changed and you will have to redo only these few changes manually instead
    of modifying the full
    ``openstack_dashboard/local/local_settings.py.example`` file.

When all settings have been migrated, it is safe to regenerate a clean diff in
order to prevent Conflicts for future migrations::

    > mv openstack_dashboard/local/local_settings.diff openstack_dashboard/local/local_settings.diff.old
    > python manage.py migrate_settings --gendiff

To start the Horizon development server use ``run_tests.sh``::

    > ./run_tests.sh --runserver localhost:9000

.. note::

    The default port for runserver is 8000 which is already consumed by
    heat-api-cfn in DevStack. If not running in DevStack
    `./run_tests.sh --runserver` will start the test server at
    `http://localhost:8000`.


.. note::

    The ``run_tests.sh`` script provides wrappers around ``manage.py``.
    For more information on manage.py which is a django, see
    `https://docs.djangoproject.com/en/dev/ref/django-admin/`


Once the Horizon server is running, point a web browser to http://localhost:9000
or to the IP and port the server is listening for.

.. note::

    The ``DevStack`` project (http://devstack.org/) can be used to install
    an OpenStack development environment from scratch. For a local.conf that
    enables most services that Horizon supports managing see
    :doc:`local.conf <ref/local_conf>`

.. note::

    The minimum required set of OpenStack services running includes the
    following:

    * Nova (compute, api, scheduler, and network)
    * Glance
    * Keystone
    * Neutron (unless nova-network is used)

    Horizon provides optional support for other services.
    See :ref:`system-requirements-label` for the supported services.
    If Keystone endpoint for a service is configured, Horizon detects it
    and enables its support automatically.


Editing Horizon's Source
========================

Although DevStack installs and configures an instance of Horizon when running
stack.sh, the preferred development setup follows the instructions above on the
server/VM running DevStack. There are several advantages to maintaining a
separate copy of the Horizon repo, rather than editing the devstack installed
copy.

    * Source code changes aren't as easily lost when running unstack.sh/stack.sh
    * The development server picks up source code changes (other than JavaScript
      and CSS due to compression and compilation) while still running.
    * Log messages and print statements go directly to the console.
    * Debugging with pdb becomes much simpler to interact with.

.. Note::
    JavaScript and CSS changes require a development server restart. Also,
    forcing a refresh of the page (e.g. using Shift-F5) in the browser is
    required to pull down non-cached versions of the CSS and JavaScript. The
    default setting in Horizon is to do compilation and compression of these
    files at server startup. If you have configured your local copy to do
    offline compression, more steps are required.


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
