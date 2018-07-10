=============================
Horizon (OpenStack Dashboard)
=============================

Horizon is a Django-based project aimed at providing a complete OpenStack
Dashboard along with an extensible framework for building new dashboards
from reusable components. The ``openstack_dashboard`` module is a reference
implementation of a Django site that uses the ``horizon`` app to provide
web-based interactions with the various OpenStack projects.

* Project documentation: https://docs.openstack.org/horizon/latest/
* Release management: https://launchpad.net/horizon
* Blueprints and feature specifications: https://blueprints.launchpad.net/horizon
* Issue tracking: https://bugs.launchpad.net/horizon
* Release notes: https://docs.openstack.org/releasenotes/horizon/

.. image:: https://governance.openstack.org/tc/badges/horizon.svg
    :target: https://governance.openstack.org/tc/reference/tags/

Using Horizon
=============

See ``doc/source/install/index.rst`` about how to install Horizon
in your OpenStack setup. It describes the example steps and
has pointers for more detailed settings and configurations.

It is also available at
`Installation Guide <https://docs.openstack.org/horizon/latest/install/>`_.

Getting Started for Developers
==============================

``doc/source/quickstart.rst`` or
`Quickstart Guide <https://docs.openstack.org/horizon/latest/contributor/quickstart.html>`_
describes how to setup Horizon development environment and start development.

Building Contributor Documentation
==================================

This documentation is written by contributors, for contributors.

The source is maintained in the ``doc/source`` directory using
`reStructuredText`_ and built by `Sphinx`_

.. _reStructuredText: http://docutils.sourceforge.net/rst.html
.. _Sphinx: http://sphinx-doc.org/

To build the docs, use::

  $ tox -e docs

Results are in the ``doc/build/html`` directory
