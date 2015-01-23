===========================
The ``run_tests.sh`` Script
===========================

.. contents:: Contents:
   :local:

Horizon ships with a script called ``run_tests.sh`` at the root of the
repository. This script provides many crucial functions for the project,
and also makes several otherwise complex tasks trivial for you as a
developer.

First Run
=========

If you start with a clean copy of the Horizon repository, the first thing
you should do is to run ``./run_tests.sh`` from the root of the repository.
This will do two things for you:

    #. Set up a virtual environment for both the ``horizon`` module and
       the ``openstack_dashboard`` project using ``./tools/install_venv.py``.
    #. Run the tests for both ``horizon`` and ``openstack_dashboard`` using
       their respective environments and verify that everything is working.

Setting up the environment the first time can take several minutes, but only
needs to be done once. If dependencies are added in the future, updating the
environments will be necessary but not as time consuming.

I just want to run the tests!
=============================

Running the full set of unit tests quickly and easily is the main goal of this
script. All you need to do is::

    ./run_tests.sh

Yep, that's it. However, for a more thorough test run you can include the
Selenium tests by using the ``--with-selenium`` flag::

    ./run_tests.sh --with-selenium

If you run horizon in a minimal installation VM, you will probably need
the following (steps for Fedora 18 minimal installation):

    #. Install these packages in the VM:
       ``yum install xorg-x11-xauth xorg-x11-fonts-Type1.noarch``.
    #. Install firefox in the VM:
       ``yum install firefox``.
    #. Connect to the VM by ``ssh -X``
       (if you run ``set|grep DISP``, you should see that the DISPLAY is set).
    #. Run
       ``./run_tests.sh --with-selenium``.

Running a subset of tests
-------------------------

Instead of running all tests, you can specify an individual directory, file,
class, or method that contains test code.

To run the tests in the ``horizon/test/tests/tables.py`` file::

    ./run_tests.sh horizon.test.tests.tables

To run the tests in the `WorkflowsTests` class in
``horizon/test/tests/workflows``::

    ./run_tests.sh horizon.test.tests.workflows:WorkflowsTests

To run just the `WorkflowsTests.test_workflow_view` test method::

    ./run_tests.sh horizon.test.tests.workflows:WorkflowsTests.test_workflow_view

Running the integration tests
-----------------------------

The Horizon integration tests treat Horizon as a black box, and similar
to Tempest must be run against an existing OpenStack system. These
tests are not run by default.

#. Update the configuration file
   `openstack_dashboard/test/integration_tests/horizon.conf` as
   required (the format is similar to the Tempest configuration file).

#. Run the tests with the following command: ::

    $ ./run_tests.sh --integration

Like for the unit tests, you can choose to only run a subset. ::

    $ ./run_tests.sh --integration openstack_dashboard.test.integration_tests.tests.test_login


Using Dashboard and Panel Templates
===================================

Horizon has a set of convenient management commands for creating new
dashboards and panels based on basic templates.

Dashboards
----------

To create a new dashboard, run the following::

    ./run_tests.sh -m startdash <dash_name>

This will create a directory with the given dashboard name, a ``dashboard.py``
module with the basic dashboard code filled in, and various other common
"boilerplate" code.

Available options:

* ``--target``: the directory in which the dashboard files should be created.
  Default: A new directory within the current directory.

Panels
------

To create a new panel, run the following::

    ./run_tests -m startpanel <panel_name>

This will create a directory with the given panel name, and ``panel.py``
module with the basic panel code filled in, and various other common
"boilerplate" code.

Available options:

* ``-d``, ``--dashboard``: The dotted python path to your dashboard app (the
  module which containers the ``dashboard.py`` file.). If not specified, the
  target dashboard should be specified in a pluggable settings file for the
  panel.
* ``--target``: the directory in which the panel files should be created.
  If the value is ``auto`` the panel will be created as a new directory inside
  the dashboard module's directory structure. Default: A new directory within
  the current directory.

Give me metrics!
================

You can generate various reports and metrics using command line arguments
to ``run_tests.sh``.

Coverage
--------

To run coverage reports::

    ./run_tests.sh --coverage

The reports are saved to ``./reports/`` and ``./coverage.xml``.

PEP8
----

You can check for PEP8 violations as well::

    ./run_tests.sh --pep8

The results are saved to ``./pep8.txt``.

PyLint
------

For more detailed code analysis you can run::

    ./run_tests.sh --pylint

The output will be saved in ``./pylint.txt``.

JsHint
------

For code analysis of JavaScript files::

    ./run_tests.sh --jshint

You need to have jshint installed before running the command.

Tab Characters
--------------

For those who dislike having a mix of tab characters and spaces for indentation
there's a command to check for that in Python, CSS, JavaScript and HTML files::

    ./run_tests.sh --tabs

This will output a total "tab count" and a list of the offending files.

Running the development server
==============================

As an added bonus, you can run Django's development server directly from
the root of the repository with ``run_tests.sh`` like so::

    ./run_tests.sh --runserver

This is effectively just an alias for::

    ./tools/with_venv.sh ./manage.py runserver

Generating the documentation
============================

You can build Horizon's documentation automatically by running::

    ./run_tests.sh --docs

The output is stored in ``./doc/build/html/``.

Updating the translation files
==============================

You can update all of the translation files for both the ``horizon`` app and
``openstack_dashboard`` project with a single command::

    ./run_tests.sh --makemessages

or, more compactly::

    ./run_tests.sh --m

Starting clean
==============

If you ever want to start clean with a new environment for Horizon, you can
run::

    ./run_tests.sh --force

That will blow away the existing environments and create new ones for you.

Non-interactive Mode
====================

There is an optional flag which will run the script in a non-interactive
(and eventually less verbose) mode::

    ./run_tests.sh --quiet

This will automatically take the default action for actions which would
normally prompt for user input such as installing/updating the environment.

Environment Backups
===================

To speed up the process of doing clean checkouts, running continuous
integration tests, etc. there are options for backing up the current
environment and restoring from a backup::

    ./run_tests.sh --restore-environment
    ./run_tests.sh --backup-environment

The environment backup is stored in ``/tmp/.horizon_environment/``.

Environment Versioning
======================

Horizon keeps track of changes to the environment by comparing the
current requirements files (``requirements.txt`` and
``test-requirements.txt``) and the files last time the virtual
environment was created or updated. If there is any difference,
the virtual environment will be update automatically when you run
``run_tests.sh``.
