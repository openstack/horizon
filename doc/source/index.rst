..
      Copyright 2012 OpenStack Foundation
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

========================================
Horizon: The OpenStack Dashboard Project
========================================

Introduction
============

Horizon is the canonical implementation of `OpenStack's Dashboard
<https://github.com/openstack/horizon>`_, which provides a web based user
interface to OpenStack services including Nova, Swift, Keystone, etc.

For a more in-depth look at Horizon and its architecture, see the
:doc:`Introduction to Horizon <intro>`.

To learn what you need to know to get going, see the :doc:`quickstart`.

Using Horizon
=============

How to use Horizon in your own projects.

.. toctree::
   :maxdepth: 1

   topics/install
   topics/deployment
   topics/settings
   topics/customizing
   topics/packaging

Developer Docs
==============

For those wishing to develop Horizon itself, or go in-depth with building
your own :class:`~horizon.Dashboard` or :class:`~horizon.Panel` classes,
the following documentation is provided.

General information
-------------------

Brief guides to areas of interest and importance when developing Horizon.

.. toctree::
   :maxdepth: 1

   intro
   quickstart
   topics/tutorial
   contributing
   testing
   plugins

Topic Guides
------------

Information on how to work with specific areas of Horizon can be found in
the following topic guides.

.. toctree::
   :maxdepth: 1

   topics/workflows
   topics/tables
   topics/policy
   topics/testing
   topics/table_actions
   topics/angularjs
   topics/javascript_testing
   topics/styling

API Reference
-------------

In-depth documentation for Horizon and its APIs.

.. toctree::
   :maxdepth: 1

   ref/run_tests
   ref/horizon
   ref/workflows
   ref/tables
   ref/tabs
   ref/forms
   ref/middleware
   ref/context_processors
   ref/decorators
   ref/exceptions
   ref/test
   ref/local_conf

Source Code Reference
---------------------

Auto-generated reference for the complete source code.

.. toctree::
   :maxdepth: 1

   sourcecode/autoindex

Release Notes
=============

.. toctree::
   :glob:
   :maxdepth: 1

   releases/*

Information
===========

.. toctree::
   :maxdepth: 1

   faq
   glossary

* :ref:`genindex`
* :ref:`modindex`
