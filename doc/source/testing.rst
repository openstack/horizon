=======================
Horizon's tests and you
=======================

How to run the tests
====================

Because Horizon is composed of both the ``horizon`` app and the
``openstack_dashboard`` reference project, there are in fact two sets of unit
tests. While they can be run individually without problem, there is an easier
way:

Included at the root of the repository is the ``run_tests.sh`` script
which invokes both sets of tests, and  optionally generates analyses on both
components in the process. This script is what Jenkins uses to verify the
stability of the project, so you should make sure you run it and it passes
before you submit any pull requests/patches.

To run the tests::

    $ ./run_tests.sh

It's also possible to :doc:`run a subset of unit tests<ref/run_tests>`.

.. seealso::

    :doc:`ref/run_tests`
        Full reference for the ``run_tests.sh`` script.


By default running the Selenium tests will open your Firefox browser (you have
to install it first, else an error is raised), and you will be able to see the
tests actions.
If you want to run the suite headless, without being able to see them (as they
are ran on Jenkins), you can run the tests::

    $ ./run_tests.sh --with-selenium --selenium-headless

Selenium will use a virtual display in this case, instead of your own. In order
to run the tests this way you have to install the dependency `xvfb`, like 
this::

    $ sudo apt-get install xvfb

for a Debian OS flavour, or for Fedora/Red Hat flavours::

    $ sudo yum install xorg-x11-server-Xvfb

If you can't run a virtual display, or would prefer not to, you can use the
PhantomJS web driver instead::

    $ ./run_tests.sh --with-selenium --selenium-phantomjs

If you need to install PhantomJS, you may do so with `npm` like this::

    $ npm -g install phantomjs


Writing tests
=============

Horizon uses Django's unit test machinery (which extends Python's ``unittest2``
library) as the core of its test suite. As such, all tests for the Python code
should be written as unit tests. No doctests please.

In general new code without unit tests will not be accepted, and every bugfix
*must* include a regression test.

For a much more in-depth discussion of testing, see the :doc:`testing topic
guide </topics/testing>`.
