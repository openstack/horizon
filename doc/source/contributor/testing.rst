=======================
Horizon's tests and you
=======================

How to run the tests
====================

Because Horizon is composed of both the ``horizon`` app and the
``openstack_dashboard`` reference project, there are in fact two sets of unit
tests. While they can be run individually without problem, there is an easier
way:

Included at the root of the repository is the ``tox.ini`` config
which invokes both sets of tests, and optionally generates analyses on both
components in the process. ``tox`` is what Jenkins uses to verify the
stability of the project, so you should make sure you run it and it passes
before you submit any pull requests/patches.

To run all tests::

    $ tox

It's also possible to run a subset of the tests. Open ``tox.ini`` in the
Horizon root directory to see a list of test environments. You can read more
about tox in general at https://tox.readthedocs.io/en/latest/.

By default running the Selenium tests will open your Firefox browser (you have
to install it first, else an error is raised), and you will be able to see the
tests actions::

    $ tox -e selenium

If you want to run the suite headless, without being able to see them (as they
are ran on Jenkins), you can run the tests::

    $ tox -e selenium-headless

Selenium will use a virtual display in this case, instead of your own. In order
to run the tests this way you have to install the dependency `xvfb`, like
this::

    $ sudo apt-get install xvfb

for a Debian OS flavour, or for Fedora/Red Hat flavours::

    $ sudo yum install xorg-x11-server-Xvfb

If you can't run a virtual display, or would prefer not to, you can use the
PhantomJS web driver instead::

    $ tox -e selenium-phantomjs

If you need to install PhantomJS, you may do so with `npm` like this::

    $ npm -g install phantomjs

Alternatively, many distributions have system packages for PhantomJS, or
it can be downloaded from http://phantomjs.org/download.html.

tox Test Environments
=====================

This is a list of test environments available to be executed by
``tox -e <name>``.

pep8
----

Runs pep8, which is a tool that checks Python code style. You can read more
about pep8 at https://www.python.org/dev/peps/pep-0008/

py27
----

Runs the Python unit tests against the current default version of Django
with Python 2.7 environment. Check ``requirements.txt`` in horizon
repository to know which version of Django is actually used.

All other dependencies are as defined by the upper-constraints file at
https://opendev.org/openstack/requirements/raw/branch/master/upper-constraints.txt

You can run a subset of the tests by passing the test path as an argument to
tox::

  $ tox -e py27 -- openstack_dashboard.dashboards.identity.users.tests

The following is more example to run a specific test class and a
specific test:

.. code-block:: console

   $ tox -e py27 -- openstack_dashboard.dashboards.identity.users.tests:UsersViewTests
   $ tox -e py27 -- openstack_dashboard.dashboards.identity.users.tests:UsersViewTests.test_index

You can also pass other arguments. For example, to drop into a live debugger
when a test fails you can use::

  $ tox -e py27 -- --pdb

py27dj18, py27dj19, py27dj110
-----------------------------

Runs the Python unit tests against Django 1.8, Django 1.9 and Django 1.10
respectively

py36
----

Runs the Python unit tests with a Python 3.6 environment.

py37
----

Runs the Python unit tests with a Python 3.7 environment.

releasenotes
------------

Outputs Horizons release notes as HTML to ``releasenotes/build/html``.

Also takes an alternative builder as an optional argument, such as
``tox -e docs -- <builder>``, which will output to
``releasenotes/build/<builder>``. Available builders are listed at
http://www.sphinx-doc.org/en/latest/builders.html

This environment also runs the documentation style checker ``doc8`` against
RST and YAML files under ``releasenotes/source`` to keep the documentation
style consistent. If you would like to run ``doc8`` manually, see **docs**
environment below.

npm
---

Installs the npm dependencies listed in ``package.json`` and runs the
JavaScript tests. Can also take optional arguments, which will be executed
as an npm script following the dependency install, instead of ``test``.

Example::

  $ tox -e npm -- lintq

docs
----

Outputs Horizons documentation as HTML to ``doc/build/html``.

Also takes an alternative builder as an optional argument, such as
``tox -e docs -- <builder>``, which will output to ``doc/build/<builder>``.
Available builders are listed at
http://www.sphinx-doc.org/en/latest/builders.html

Example::

  $ tox -e docs -- latexpdf

This environment also runs the documentation style checker ``doc8`` against
RST files under ``doc/source`` to keep the documentation style consistent.
If you would like to run ``doc8`` manually, run:

.. code-block:: console

   # Activate virtualenv
   $ . .tox/docs/bin/activate
   $ doc8 doc/source

Writing tests
=============

Horizon uses Django's unit test machinery (which extends Python's ``unittest2``
library) as the core of its test suite. As such, all tests for the Python code
should be written as unit tests. No doctests please.

In general new code without unit tests will not be accepted, and every bugfix
*must* include a regression test.

For a much more in-depth discussion of testing, see the :ref:`testing topic
guide <topics-testing>`.
