..
      Copyright 2011 OpenStack, LLC
      All Rights Reserved.

      Licensed under the Apache License, Version 2.0 (the "License"); you may
      not use this file except in compliance with the License. You may obtain
      a copy of the License at

          http://www.apache.org/licenses/LICENSE-2.0

      Unless required by applicable law or agreed to in writing, software
      distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
      WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
      License for the specific language governing permissions and limitations
      under the License.

===============
Testing Horizon
===============

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

.. seealso::

    :doc:`ref/run_tests`
        Full reference for the ``run_tests.sh`` script.

How to write good tests
=======================

Horizon uses Django's unit test machinery (which extends Python's ``unittest2``
library) as the core of it's test suite. As such, all tests for the Python code
should be written as unit tests. No doctests please.

A few pointers for writing good tests:

    * Write tests as you go--If you save them to the end you'll write less of
      them and they'll often miss large chunks of code.
    * Keep it as simple as possible--Make sure each test tests one thing
      and tests it thoroughly.
    * Think about all the possible inputs your code could have--It's usually
      the edge cases that end up revealing bugs.
    * Use ``coverage.py`` to find out what code is *not* being tested.

In general new code without unit tests will not be accepted, and every bugfix
*must* include a regression test.
