===========================
View cloud usage statistics
===========================

The Telemetry service provides user-level usage data for
OpenStack-based clouds, which can be used for customer billing, system
monitoring, or alerts. Data can be collected by notifications sent by
existing OpenStack components (for example, usage events emitted from
Compute) or by polling the infrastructure (for example, libvirt).

.. note::

   You can only view metering statistics on the dashboard (available
   only to administrators).
   The Telemetry service must be set up and administered through the
   :command:`ceilometer` command-line interface (CLI).

   For basic administration information, refer to the `Measure Cloud
   Resources <https://docs.openstack.org/user-guide/cli-ceilometer.html>`_
   chapter in the OpenStack End User Guide.

.. _dashboard-view-resource-stats:

View resource statistics
~~~~~~~~~~~~~~~~~~~~~~~~

#. Log in to the dashboard and select the :guilabel:`admin` project
   from the drop-down list.

#. On the :guilabel:`Admin` tab, click the :guilabel:`Resource Usage` category.

#. Click the:

   * :guilabel:`Usage Report` tab to view a usage report per project
     by specifying the time period (or even use a calendar to define
     a date range).

   * :guilabel:`Stats` tab to view a multi-series line chart with
     user-defined meters. You group by project, define the value type
     (min, max, avg, or sum), and specify the time period (or even use
     a calendar to define a date range).
