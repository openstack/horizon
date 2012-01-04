OpenStack Dashboard (Horizon)
-----------------------------

The OpenStack Dashboard is a Django based reference implementation of a web
based management interface for OpenStack.

It is based on the ``horizon`` module, which is designed to be a generic Django
app that can be re-used in other projects.

For more information about how to get started with the OpenStack Dashboard,
view the README file in the openstack-dashboard folder.

For more information about working directly with ``horizon``, see the
README file in the ``horizon`` folder.

For release management:

 * https://launchpad.net/horizon

For blueprints and feature specifications:

 * https://blueprints.launchpad.net/horizon

For issue tracking:

 * https://bugs.launchpad.net/horizon


Project Structure and Testing:
------------------------------

This project is a bit different from other OpenStack projects in that it has
two very distinct components underneath it: ``horizon``, and
``openstack-dashboard``.

The ``horizon`` directory holds the generic libraries and components that can
be used in any Django project.

The ``openstack-dashboard`` directory contains a reference Django project that
uses ``horizon``.

For development, both pieces share an environment which (by default) is
built with the ``tools/install_venv.py`` script. That script creates a
virtualenv and installs all the necessary packages.

If dependencies are added to either ``horizon`` or ``openstack-dashboard``,
they should be added to ``tools/pip-requires``.

The ``run_tests.sh`` script invokes tests and analyses on both of these
components in its process, and is what Jenkins uses to verify the
stability of the project. If run before an environment is set up, it will
ask if you wish to install one.

To run the tests::

    $ ./run_tests.sh

Building Contributor Documentation
----------------------------------

This documentation is written by contributors, for contributors.

The source is maintained in the ``docs/source`` folder using
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
