.. _quickstart:

==========
Quickstart
==========

..  Note ::

    This section has been tested for Horizon on Ubuntu (16.04-64) and RPM-based
    (RHEL 7.x) distributions. Feel free to add notes and any changes according
    to your experiences or operating system.

Linux Systems
=============

Install the prerequisite packages.

On Ubuntu

.. code-block:: console

    $ sudo apt-get install git python-pip

On RPM-based distributions (e.g., Fedora/RHEL/CentOS/Scientific Linux)

.. code-block:: console

    $ sudo yum install gcc git-core python-devel python-virtualenv openssl-devel libffi-devel which

.. note::

    Some tests rely on the Chrome web browser being installed. While the above
    requirements will allow you to run and manually test Horizon, you will
    need to install Chrome to run the full test suite.

Setup
=====

To begin setting up a Horizon development environment simply clone the Horizon
git repository from https://opendev.org/openstack/horizon

.. code-block:: console

    $ git clone https://opendev.org/openstack/horizon

Next you will need to configure Horizon by adding a ``local_settings.py`` file.
A good starting point is to use the example config with the following command,
from within the ``horizon`` directory.

.. code-block:: console

    $ cp openstack_dashboard/local/local_settings.py.example openstack_dashboard/local/local_settings.py

Horizon connects to the rest of OpenStack via a Keystone service catalog. By
default Horizon looks for an endpoint at ``http://localhost:5000/v3``; this
can be customised by modifying the ``OPENSTACK_HOST`` and
``OPENSTACK_KEYSTONE_URL`` values in
``openstack_dashboard/local/local_settings.py``

.. note::

    The DevStack project (http://devstack.org/) can be used to install
    an OpenStack development environment from scratch. For a local.conf that
    enables most services that Horizon supports managing, see
    :ref:`local-conf`

Horizon uses ``tox`` to manage virtual environments for testing and other
development tasks. You can install it with

.. code-block:: console

    $ pip install tox

The ``tox`` environments provide wrappers around ``manage.py``. For more
information on ``manage.py``, which is a Django command, see
https://docs.djangoproject.com/en/dev/ref/django-admin/

To start the Horizon development server use the command below

.. code-block:: console

    $ tox -e runserver

.. note::

    The default port for runserver is 8000 which might be already consumed by
    heat-api-cfn in DevStack. If running in DevStack
    ``tox -e runserver -- localhost:9000`` will start the test server at
    ``http://localhost:9000``. If you use ``tox -e runserver`` for developments,
    then configure ``SESSION_ENGINE`` to
    ``django.contrib.sessions.backends.signed_cookies`` in
    ``openstack_dashboard/local/local_settings.py`` file.

Once the Horizon server is running, point a web browser to ``http://localhost``
or to the IP and port the server is listening for. Enter your Keystone
credentials, log in and you'll be presented with the Horizon dashboard.
Congratulations!

Managing Settings
=================

You can save changes you made to
``openstack_dashboard/local/local_settings.py`` with the following command:

.. code-block:: console

    $ python manage.py migrate_settings --gendiff

.. note::

    This creates a ``local_settings.diff`` file which is a diff between
    ``local_settings.py`` and ``local_settings.py.example``

If you upgrade Horizon, you might need to update your
``openstack_dashboard/local/local_settings.py`` file with new parameters from
``openstack_dashboard/local/local_settings.py.example`` to do so, first update
Horizon

.. code-block:: console

    $ git remote update && git pull --ff-only origin master

Then update your  ``openstack_dashboard/local/local_settings.py`` file

.. code-block:: console

    $ mv openstack_dashboard/local/local_settings.py openstack_dashboard/local/local_settings.py.old
    $ python manage.py migrate_settings

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
order to prevent Conflicts for future migrations

.. code-block:: console

    $ mv openstack_dashboard/local/local_settings.diff openstack_dashboard/local/local_settings.diff.old
    $ python manage.py migrate_settings --gendiff

Editing Horizon's Source
========================

Although DevStack installs and configures an instance of Horizon when running
stack.sh, the preferred development setup follows the instructions above on the
server/VM running DevStack. There are several advantages to maintaining a
separate copy of the Horizon repo, rather than editing the DevStack installed
copy.

- Source code changes aren't as easily lost when running ``unstack.sh`` /
  ``stack.sh``
- The development server picks up source code changes while still running.
- Log messages and print statements go directly to the console.
- Debugging with ``pdb`` becomes much simpler to interact with.

.. note::

  To ensure that JS and CSS changes are picked up without a server restart, you
  can disable compression with ``COMPRESS_ENABLED = False`` in your local
  settings file.

Horizon's Structure
===================

This project is a bit different from other OpenStack projects in that it has
two very distinct components underneath it: ``horizon``, and
``openstack_dashboard``.

The ``horizon`` directory holds the generic libraries and components that can
be used in any Django project.

The ``openstack_dashboard`` directory contains a reference Django project that
uses ``horizon``.

If dependencies are added to either ``horizon`` or ``openstack_dashboard``,
they should be added to ``requirements.txt``.

Project Structure
=================

Dashboard configuration
-----------------------

To add a new dashboard to your project, you need to add a configuration file to
``openstack_dashboard/local/enabled`` directory. For more information on this,
see :ref:`pluggable-settings-label`.

URLs
----

Then you add a single line to your project's ``urls.py``

.. code-block:: python

    url(r'', include(horizon.urls)),

Those urls are automatically constructed based on the registered Horizon apps.
If a different URL structure is desired it can be constructed by hand.

Templates
---------

Pre-built template tags generate navigation. In your ``nav.html``
template you might have the following

.. code-block:: htmldjango

    {% load horizon %}

    <div class='nav'>
      {% horizon_main_nav %}
    </div>

And in your ``sidebar.html`` you might have

.. code-block:: htmldjango

    {% load horizon %}

    <div class='sidebar'>
      {% horizon_dashboard_nav %}
    </div>

These template tags are aware of the current "active" dashboard and panel
via template context variables and will render accordingly.

Application Design
==================

Structure
---------

An application would have the following structure (we'll use project as
an example)

.. code-block:: console

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

Inside of ``dashboard.py`` you would have a class definition and the
registration process

.. code-block:: python

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
you register it in a ``panel.py`` file

.. code-block:: python

    import horizon

    from openstack_dashboard.dashboards.project import dashboard


    class Images(horizon.Panel):
        name = "Images"
        slug = 'images'
        permissions = ('openstack.roles.admin', 'openstack.service.image')
        policy_rules = (('endpoint', 'endpoint:rule'),)

    # You could also register your panel with another application's dashboard
    dashboard.Project.register(Images)

By default a :class:`~horizon.Panel` class looks for a ``urls.py`` file in the
same directory as ``panel.py`` to include in the rollup of url patterns from
panels to dashboards to Horizon, resulting in a wholly extensible, configurable
URL structure.

Policy rules are defined in ``horizon/openstack_dashboard/conf/``. Permissions
are inherited from Keystone and take either the form
'openstack.roles.role_name' or 'openstack.services.service_name' for the user's
roles in keystone and the services in their service catalog.
