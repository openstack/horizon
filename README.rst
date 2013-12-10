=============================
Horizon (OpenStack Dashboard)
=============================

Horizon is a Django-based project aimed at providing a complete OpenStack
Dashboard along with an extensible framework for building new dashboards
from reusable components. The ``openstack_dashboard`` module is a reference
implementation of a Django site that uses the ``horizon`` app to provide
web-based interactions with the various OpenStack projects.

For release management:

 * https://launchpad.net/horizon

For blueprints and feature specifications:

 * https://blueprints.launchpad.net/horizon

For issue tracking:

 * https://bugs.launchpad.net/horizon


Getting Started
===============

For local development, first create a virtualenv for the project.
In the ``tools`` directory there is a script to create one for you:

  $ python tools/install_venv.py

Alternatively, the ``run_tests.sh`` script will also install the environment
for you and then run the full test suite to verify everything is installed
and functioning correctly.

Now that the virtualenv is created, you need to configure your local
environment.  To do this, create a ``local_settings.py`` file in the
``openstack_dashboard/local/`` directory.  There is a
``local_settings.py.example`` file there that may be used as a template.

If all is well you should able to run the development server locally:

  $ tools/with_venv.sh manage.py runserver

or, as a shortcut::

  $ ./run_tests.sh --runserver


Setting Up OpenStack
====================

The recommended tool for installing and configuring the core OpenStack
components is `Devstack`_. Refer to their documentation for getting
Nova, Keystone, Glance, etc. up and running.

.. _Devstack: http://devstack.org/

.. note::

    The minimum required set of OpenStack services running includes the
    following:

    * Nova (compute, api, scheduler, network, *and* volume services)
    * Glance
    * Keystone

    Optional support is provided for Swift.


Development
===========

For development, start with the getting started instructions above.
Once you have a working virtualenv and all the necessary packages, read on.

If dependencies are added to either ``horizon`` or ``openstack_dashboard``,
they should be added to ``requirements.txt``.

The ``run_tests.sh`` script invokes tests and analyses on both of these
components in its process, and it is what Jenkins uses to verify the
stability of the project. If run before an environment is set up, it will
ask if you wish to install one.

To run the unit tests::

    $ ./run_tests.sh

Building Contributor Documentation
==================================

This documentation is written by contributors, for contributors.

The source is maintained in the ``doc/source`` folder using
`reStructuredText`_ and built by `Sphinx`_

.. _reStructuredText: http://docutils.sourceforge.net/rst.html
.. _Sphinx: http://sphinx.pocoo.org/

* Building Automatically::

    $ ./run_tests.sh --docs

* Building Manually::

    $ export DJANGO_SETTINGS_MODULE=local.local_settings
    $ python doc/generate_autodoc_index.py
    $ sphinx-build -b html doc/source build/sphinx/html

Results are in the `build/sphinx/html` directory
