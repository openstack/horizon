=======================
Horizon's tests and you
=======================

How to run the tests
====================

Because Horizon is composed of both the ``horizon`` app and the
``openstack-dashboard`` reference project, there are in fact two sets of unit
tests. While they can be run individually without problem, there is an easier
way:

Included at the root of the repository is the ``run_tests.sh`` script
which invokes both sets of tests, and  optionally generates analyses on both
components in the process. This script is what what Jenkins uses to verify the
stability of the project, so you should make sure you run it and it passes
before you submit any pull requests/patches.

To run the tests::

    $ ./run_tests.sh
   
It's also possible to :doc:`run a subset of unit tests<ref/run_tests>`.

.. seealso::

    :doc:`ref/run_tests`
        Full reference for the ``run_tests.sh`` script.

Writing tests
=============

Horizon uses Django's unit test machinery (which extends Python's ``unittest2``
library) as the core of its test suite. As such, all tests for the Python code
should be written as unit tests. No doctests please.

In general new code without unit tests will not be accepted, and every bugfix
*must* include a regression test.

For a much more in-depth discussion of testing, see the :doc:`testing topic
guide </topics/testing>`.
