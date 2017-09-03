.. _dashboard-set-quotas:

======================
View and manage quotas
======================

.. |nbsp| unicode:: 0xA0 .. nbsp
   :trim:

To prevent system capacities from being exhausted without notification,
you can set up quotas. Quotas are operational limits. For example, the
number of gigabytes allowed for each project can be controlled so that
cloud resources are optimized. Quotas can be enforced at both the project
and the project-user level.

Typically, you change quotas when a project needs more than ten
volumes or 1 |nbsp| TB on a compute node.

Using the Dashboard, you can view default Compute and Block Storage
quotas for new projects, as well as update quotas for existing projects.

.. note::

   Using the command-line interface, you can manage quotas for
   `the OpenStack Compute service <https://docs.openstack.org/nova/latest/admin/quotas.html>`__,
   `the OpenStack Block Storage service <https://docs.openstack.org/cinder/latest/cli/cli-set-quotas.html>`__,
   and the OpenStack Networking service (For CLI details,
   see `OpenStackClient CLI reference
   <https://docs.openstack.org/python-openstackclient/latest/cli/command-objects/quota.html>`_).
   Additionally, you can update Compute service quotas for
   project users.

.. NOTE: Admin guide contents on the networking service quota
   has not been migrated to neutron. Update the link once it is recovered.

The following table describes the Compute and Block Storage service quotas:

.. _compute_quotas:

**Quota Descriptions**

+--------------------+------------------------------------+---------------+
|     Quota Name     |     Defines the number of          |   Service     |
+====================+====================================+===============+
| Gigabytes          | Volume gigabytes allowed for       | Block Storage |
|                    | each project.                      |               |
+--------------------+------------------------------------+---------------+
| Instances          | Instances allowed for each         | Compute       |
|                    | project.                           |               |
+--------------------+------------------------------------+---------------+
| Injected Files     | Injected files allowed for each    | Compute       |
|                    | project.                           |               |
+--------------------+------------------------------------+---------------+
| Injected File      | Content bytes allowed for each     | Compute       |
| Content Bytes      | injected file.                     |               |
+--------------------+------------------------------------+---------------+
| Keypairs           | Number of keypairs.                | Compute       |
+--------------------+------------------------------------+---------------+
| Metadata Items     | Metadata items allowed for each    | Compute       |
|                    | instance.                          |               |
+--------------------+------------------------------------+---------------+
| RAM (MB)           | RAM megabytes allowed for          | Compute       |
|                    | each instance.                     |               |
+--------------------+------------------------------------+---------------+
| Security Groups    | Security groups allowed for each   | Compute       |
|                    | project.                           |               |
+--------------------+------------------------------------+---------------+
| Security Group     | Security group rules allowed for   | Compute       |
| Rules              | each project.                      |               |
+--------------------+------------------------------------+---------------+
| Snapshots          | Volume snapshots allowed for       | Block Storage |
|                    | each project.                      |               |
+--------------------+------------------------------------+---------------+
| VCPUs              | Instance cores allowed for each    | Compute       |
|                    | project.                           |               |
+--------------------+------------------------------------+---------------+
| Volumes            | Volumes allowed for each           | Block Storage |
|                    | project.                           |               |
+--------------------+------------------------------------+---------------+

.. _dashboard_view_quotas_procedure:

View default project quotas
~~~~~~~~~~~~~~~~~~~~~~~~~~~

#. Log in to the dashboard and select the :guilabel:`admin` project
   from the drop-down list.

#. On the :guilabel:`Admin` tab, open the :guilabel:`System` tab
   and click the :guilabel:`Defaults` category.

#. The default quota values are displayed.

.. note::

   You can sort the table by clicking on either the
   :guilabel:`Quota Name` or :guilabel:`Limit` column headers.

.. _dashboard_update_project_quotas:

Update project quotas
~~~~~~~~~~~~~~~~~~~~~

#. Log in to the dashboard and select the :guilabel:`admin` project
   from the drop-down list.

#. On the :guilabel:`Admin` tab, open the :guilabel:`System` tab
   and click the :guilabel:`Defaults` category.

#. Click the :guilabel:`Update Defaults` button.

#. In the :guilabel:`Update Default Quotas` window,
   you can edit the default quota values.

#. Click the :guilabel:`Update Defaults` button.

.. note::

   The dashboard does not show all possible project quotas.
   To view and update the quotas for a service, use its
   command-line client. See `OpenStack Administrator Guide
   <https://docs.openstack.org/admin-guide/cli-set-quotas.html>`_.
