=================================
Create and manage host aggregates
=================================

Host aggregates enable administrative users to assign key-value pairs to
groups of machines.

Each node can have multiple aggregates and each aggregate can have
multiple key-value pairs. You can assign the same key-value pair to
multiple aggregates.

The scheduler uses this information to make scheduling decisions.
For information, see
`Scheduling <https://docs.openstack.org/nova/latest/admin/configuration/schedulers.html>`__.

To create a host aggregate
~~~~~~~~~~~~~~~~~~~~~~~~~~

#. Log in to the Dashboard and select the :guilabel:`admin` project
   from the drop-down list.

#. On the :guilabel:`Admin` tab, open the :guilabel:`Compute` tab and click
   the :guilabel:`Host Aggregates` category.

#. Click :guilabel:`Create Host Aggregate`.

#. In the :guilabel:`Create Host Aggregate` dialog box, enter or select the
   following values on the :guilabel:`Host Aggregate Information` tab:

   -  :guilabel:`Name`: The host aggregate name.

   -  :guilabel:`Availability Zone`: The cloud provider defines the default
      availability zone, such as ``us-west``, ``apac-south``, or
      ``nova``. You can target the host aggregate, as follows:

      -  When the host aggregate is exposed as an availability zone,
         select the availability zone when you launch an instance.

      -  When the host aggregate is not exposed as an availability zone,
         select a flavor and its extra specs to target the host
         aggregate.

#. Assign hosts to the aggregate using the :guilabel:`Manage Hosts within
   Aggregate` tab in the same dialog box.

   To assign a host to the aggregate, click **+** for the host. The host
   moves from the :guilabel:`All available hosts` list to the
   :guilabel:`Selected hosts` list.

You can add one host to one or more aggregates. To add a host to an
existing aggregate, edit the aggregate.

To manage host aggregates
~~~~~~~~~~~~~~~~~~~~~~~~~

#. Select the :guilabel:`admin` project from the drop-down list at the top
   of the page.

#. On the :guilabel:`Admin` tab, open the :guilabel:`Compute` tab and click
   the :guilabel:`Host Aggregates` category.

   -  To edit host aggregates, select the host aggregate that you want
      to edit. Click :guilabel:`Edit Host Aggregate`.

      In the :guilabel:`Edit Host Aggregate` dialog box, you can change the
      name and availability zone for the aggregate.

   -  To manage hosts, locate the host aggregate that you want to edit
      in the table. Click :guilabel:`More` and select :guilabel:`Manage Hosts`.

      In the :guilabel:`Add/Remove Hosts to Aggregate` dialog box,
      click **+** to assign a host to an aggregate. Click **-** to
      remove a host that is assigned to an aggregate.

   -  To delete host aggregates, locate the host aggregate that you want
      to edit in the table. Click :guilabel:`More` and select
      :guilabel:`Delete Host Aggregate`.
