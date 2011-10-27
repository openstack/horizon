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

========================
Horizon for Contributors
========================

Horizon is the canonical implementation of `Openstack's Dashboard
<https://github.com/openstack/horizon>`_, which provides a web based user
interface to OpenStack services including Nova, Swift, Keystone, and Quantum.

This document describes horizon for contributors of the project.

Project Structure
=================

This project is a bit different from other Openstack projects in that it has
two very distinct components underneath it:

* django-openstack
* openstack-dashboard

Django-openstack holds the generic libraries and components that can be
used in any Django project. In testing, this component is set up with
buildout (see run_tests.sh), and any dependencies that get added need to
be added to the django-openstack/buildout.cfg file.

Openstack-dashboard is a reference django project that uses django-openstack
and is built with a virtualenv and tested through that environment. If
depdendencies are added that the reference django project needs, they
should be added to openstack-dashboard/tools/pip-requires.

Contents:
---------

.. toctree::
   :maxdepth: 1

   testing

Developer Docs
--------------

.. toctree::
   :maxdepth: 1

   sourcecode/autoindex


Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

