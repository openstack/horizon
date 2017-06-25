==========================
Deployment & Configuration
==========================

This section describes how to install and configure the dashboard
on the controller node.

The only core service required by the dashboard is the Identity service.
You can use the dashboard in combination with other services, such as
Image service, Compute, and Networking. You can also use the dashboard
in environments with stand-alone services such as Object Storage.

.. note::

   This section assumes proper installation, configuration, and operation
   of the Identity service using the Apache HTTP server and Memcached
   service.

Installing from Packages
========================

.. toctree::
   :maxdepth: 1
   :glob:

   install-*
   verify-*
   next-steps

Installing from Source
======================

.. toctree::
   :maxdepth: 1

   from-source.rst
   settings.rst
   customizing.rst
   plugin-registry.rst
