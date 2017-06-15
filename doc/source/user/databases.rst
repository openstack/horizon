===========================
Create and manage databases
===========================

The Database service provides scalable and reliable cloud provisioning
functionality for both relational and non-relational database engines.
Users can quickly and easily use database features without the burden of
handling complex administrative tasks.

.. _dashboard_create_db_instance:

Create a database instance
~~~~~~~~~~~~~~~~~~~~~~~~~~

**Prerequisites.** Before you create a database instance, you need to
configure a default datastore and make sure you have an appropriate
flavor for the type of database instance you want.

#. **Configure a default datastore.**

   Because the dashboard does not let you choose a specific datastore to
   use with an instance, you need to configure a default datastore. The
   dashboard then uses the default datastore to create the instance.

   #. Add the following line to ``/etc/trove/trove.conf``:

      .. code-block:: console

         default_datastore = DATASTORE_NAME

      Replace ``DATASTORE_NAME`` with the name that the administrative
      user set when issuing the :command:`trove-manage` command to create the
      datastore. You can use the trove :command:`datastore-list` command to
      display the datastores that are available in your environment.

      For example, if your MySQL data store name is set to ``mysql``,
      your entry would look like this:

      .. code-block:: console

         default_datastore = mysql

   #. Restart Database services on the controller node:

      .. code-block:: console

         # service trove-api restart
         # service trove-taskmanager restart
         # service trove-conductor restart

#. **Verify flavor.**

   Make sure an appropriate flavor exists for the type of
   database instance you want.

**Create database instance.** Once you have configured a default
datastore and verified that you have an appropriate flavor, you can
create a database instance.

#. Log in to the dashboard.

#. From the CURRENT PROJECT on the :guilabel:`Project` tab, select the
   appropriate project.

#. On the :guilabel:`Project` tab, open the :guilabel:`Database` tab and
   click :guilabel:`Instances` category.  This lists the instances that
   already exist in your environment.

#. Click :guilabel:`Launch Instance`.

#. In the :guilabel:`Launch Database` dialog box, specify the following values.

   Details

   :guilabel:`Database Name`: Specify a name for the database instance.

   :guilabel:`Flavor`: Select an appropriate flavor for the instance.

   :guilabel:`Volume Size`: Select a volume size. Volume size is expressed in
   GB.

   :guilabel:`Initialize Databases`: Initial Database

   Optionally provide a comma separated list of databases to create, for
   example:

   ``database1``, ``database2``, ``database3``

   :guilabel:`Initial Admin User`: Create an initial admin user. This user will
   have access to all the databases you create.

   :guilabel:`Password`: Specify a password associated with the initial admin
   user you just named.

   :guilabel:`Host`: Optionally, allow the user to connect only from this host.
   If you do not specify a host, this user will be allowed to connect from
   anywhere.

#. Click the :guilabel:`Launch` button. The new database instance appears in
   the databases list.

Backup and restore a database
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

You can use Database services to backup a database and store the backup
artifact in the Object Storage service. Later on, if the original
database is damaged, you can use the backup artifact to restore the
database. The restore process creates a database instance.

This example shows you how to back up and restore a MySQL database.

To backup the database instance
-------------------------------

#. Log in to the dashboard.

#. From the CURRENT PROJECT on the :guilabel:`Project` tab, select the
   appropriate project.

#. On the :guilabel:`Project` tab, open the :guilabel:`Database` tab and
   click :guilabel:`Instances` category. This displays the existing
   instances in your system.

#. Click :guilabel:`Create Backup`.

#. In the :guilabel:`Backup Database` dialog box, specify the following
   values:

   Name

   Specify a name for the backup.

   Database Instance

   Select the instance you want to back up.

#. Click :guilabel:`Backup`. The new backup appears in the backup list.

To restore a database instance
------------------------------

Now assume that your original database instance is damaged and you
need to restore it. You do the restore by using your backup to create
a new database instance.

#. Log in to the dashboard.

#. From the CURRENT PROJECT on the :guilabel:`Project` tab, select the
   appropriate project.

#. On the :guilabel:`Project` tab, open the :guilabel:`Database` tab and
   click :guilabel:`Backups` category. This lists the available backups.

#. Check the backup you want to use and click :guilabel:`Restore Backup`.

#. In the :guilabel:`Launch Database` dialog box, specify the values you
   want for the new database instance.

#. Click the :guilabel:`Restore From Database` tab and make sure that this
   new instance is based on the correct backup.

#. Click :guilabel:`Launch`.

   The new instance appears in the database instances list.

Update a database instance
~~~~~~~~~~~~~~~~~~~~~~~~~~

You can change various characteristics of a database instance,
such as its volume size and flavor.

To change the volume size of an instance
----------------------------------------

#. Log in to the dashboard.

#. From the CURRENT PROJECT on the :guilabel:`Project` tab, select the
   appropriate project.

#. On the :guilabel:`Project` tab, open the :guilabel:`Database` tab and
   click :guilabel:`Instances` category. This displays the existing
   instances in your system.

#. Check the instance you want to work with.
   In the :guilabel:`Actions` column, expand the drop down menu
   and select :guilabel:`Resize Volume`.

#. In the :guilabel:`Resize Database Volume` dialog box,
   fill in the :guilabel:`New Size` field with an integer indicating
   the new size you want for the instance. Express the size in GB, and
   note that the new size must be larger than the current size.

#. Click :guilabel:`Resize Database Volume`.

To change the flavor of an instance
-----------------------------------

#. Log in to the dashboard.

#. From the CURRENT PROJECT on the :guilabel:`Project` tab, select the
   appropriate project.

#. On the :guilabel:`Project` tab, open the :guilabel:`Database` tab and
   click :guilabel:`Instances` category. This displays the existing
   instances in your system.

#. Check the instance you want to work with. In the
   :guilabel:`Actions` column, expand the drop down menu and
   select :guilabel:`Resize Instance`.

#. In the :guilabel:`Resize Database Instance` dialog box,
   expand the drop down menu in the :guilabel:`New Flavor` field.
   Select the new flavor you want for the instance.

#. Click :guilabel:`Resize Database Instance`.

