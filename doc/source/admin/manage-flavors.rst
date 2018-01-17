==============
Manage flavors
==============

In OpenStack, a flavor defines the compute, memory, and storage
capacity of a virtual server, also known as an instance. As an
administrative user, you can create, edit, and delete flavors.

As of Newton, there are no default flavors.  The following table
lists the default flavors for Mitaka and earlier.

============  =========  ===============  =============
 Flavor         VCPUs      Disk (in GB)     RAM (in MB)
============  =========  ===============  =============
 m1.tiny        1          1                512
 m1.small       1          20               2048
 m1.medium      2          40               4096
 m1.large       4          80               8192
 m1.xlarge      8          160              16384
============  =========  ===============  =============

Create flavors
~~~~~~~~~~~~~~

#. Log in to the Dashboard and select the :guilabel:`admin` project
   from the drop-down list.
#. In the :guilabel:`Admin` tab, open the :guilabel:`Compute`
   tab and click the :guilabel:`Flavors` category.
#. Click :guilabel:`Create Flavor`.
#. In the :guilabel:`Create Flavor` window, enter or select the
   parameters for the flavor in the :guilabel:`Flavor Information` tab.

   .. figure:: figures/create_flavor.png

      **Dashboard — Create Flavor**

   =========================  =======================================
    **Name**                   Enter the flavor name.
    **ID**                     Unique ID (integer or UUID) for the
                               new flavor. If specifying 'auto', a
                               UUID will be automatically generated.
    **VCPUs**                  Enter the number of virtual CPUs to
                               use.
    **RAM (MB)**               Enter the amount of RAM to use, in
                               megabytes.
    **Root Disk (GB)**         Enter the amount of disk space in
                               gigabytes to use for the root (/)
                               partition.
    **Ephemeral Disk (GB)**    Enter the amount of disk space in
                               gigabytes to use for the ephemeral
                               partition. If unspecified, the value
                               is 0 by default.

                               Ephemeral disks offer machine local
                               disk storage linked to the lifecycle
                               of a VM instance. When a VM is
                               terminated, all data on the ephemeral
                               disk is lost. Ephemeral disks are not
                               included in any snapshots.
    **Swap Disk (MB)**         Enter the amount of swap space (in
                               megabytes) to use. If unspecified,
                               the default is 0.
    **RX/TX Factor**           Optional property allows servers with
                               a different bandwidth to be created
                               with the RX/TX Factor. The default
                               value is 1. That is, the new bandwidth
                               is the same as that of the attached
                               network.
   =========================  =======================================

#. In the :guilabel:`Flavor Access` tab, you can control access to
   the flavor by moving projects from the :guilabel:`All Projects`
   column to the :guilabel:`Selected Projects` column.

   Only projects in the :guilabel:`Selected Projects` column can
   use the flavor. If there are no projects in the right column,
   all projects can use the flavor.
#. Click :guilabel:`Create Flavor`.

Update flavors
~~~~~~~~~~~~~~

#. Log in to the Dashboard and select the :guilabel:`admin` project
   from the drop-down list.
#. In the :guilabel:`Admin` tab, open the :guilabel:`Compute` tab
   and click the :guilabel:`Flavors` category.
#. Select the flavor that you want to edit. Click :guilabel:`Edit
   Flavor`.
#. In the :guilabel:`Edit Flavor` window, you can change the flavor
   name, VCPUs, RAM, root disk, ephemeral disk, and swap disk values.
#. Click :guilabel:`Save`.

Update Metadata
~~~~~~~~~~~~~~~

#. Log in to the Dashboard and select the :guilabel:`admin` project
   from the drop-down list.
#. In the :guilabel:`Admin` tab, open the :guilabel:`Compute` tab
   and click the :guilabel:`Flavors` category.
#. Select the flavor that you want to update. In the drop-down
   list, click :guilabel:`Update Metadata` or click :guilabel:`No` or
   :guilabel:`Yes` in the :guilabel:`Metadata` column.
#. In the :guilabel:`Update Flavor Metadata` window, you can customize
   some metadata keys, then add it to this flavor and set them values.
#. Click :guilabel:`Save`.

   **Optional metadata keys**

   +-------------------------------+-------------------------------+
   |                               | quota:cpu_shares              |
   |                               +-------------------------------+
   | **CPU limits**                | quota:cpu_period              |
   |                               +-------------------------------+
   |                               | quota:cpu_limit               |
   |                               +-------------------------------+
   |                               | quota:cpu_reservation         |
   |                               +-------------------------------+
   |                               | quota:cpu_quota               |
   +-------------------------------+-------------------------------+
   |                               | quota:disk_read_bytes_sec     |
   |                               +-------------------------------+
   | **Disk tuning**               | quota:disk_read_iops_sec      |
   |                               +-------------------------------+
   |                               | quota:disk_write_bytes_sec    |
   |                               +-------------------------------+
   |                               | quota:disk_write_iops_sec     |
   |                               +-------------------------------+
   |                               | quota:disk_total_bytes_sec    |
   |                               +-------------------------------+
   |                               | quota:disk_total_iops_sec     |
   +-------------------------------+-------------------------------+
   |                               | quota:vif_inbound_average     |
   |                               +-------------------------------+
   | **Bandwidth I/O**             | quota:vif_inbound_burst       |
   |                               +-------------------------------+
   |                               | quota:vif_inbound_peak        |
   |                               +-------------------------------+
   |                               | quota:vif_outbound_average    |
   |                               +-------------------------------+
   |                               | quota:vif_outbound_burst      |
   |                               +-------------------------------+
   |                               | quota:vif_outbound_peak       |
   +-------------------------------+-------------------------------+
   | **Watchdog behavior**         | hw:watchdog_action            |
   +-------------------------------+-------------------------------+
   |                               | hw_rng:allowed                |
   |                               +-------------------------------+
   | **Random-number generator**   | hw_rng:rate_bytes             |
   |                               +-------------------------------+
   |                               | hw_rng:rate_period            |
   +-------------------------------+-------------------------------+

   For information about supporting metadata keys, see the
   the Compute service documentation.

Delete flavors
~~~~~~~~~~~~~~

#. Log in to the Dashboard and select the :guilabel:`admin` project
   from the drop-down list.
#. In the :guilabel:`Admin` tab, open the :guilabel:`Compute` tab
   and click the :guilabel:`Flavors` category.
#. Select the flavors that you want to delete.
#. Click :guilabel:`Delete Flavors`.
#. In the :guilabel:`Confirm Delete Flavors` window, click
   :guilabel:`Delete Flavors` to confirm the deletion. You cannot
   undo this action.
