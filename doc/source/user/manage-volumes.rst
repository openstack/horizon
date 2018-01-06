=========================
Create and manage volumes
=========================

Volumes are block storage devices that you attach to instances to enable
persistent storage. You can attach a volume to a running instance or
detach a volume and attach it to another instance at any time. You can
also create a snapshot from or delete a volume. Only administrative
users can create volume types.

Create a volume
~~~~~~~~~~~~~~~

#. Log in to the dashboard.

#. Select the appropriate project from the drop down menu at the top left.

#. On the :guilabel:`Project` tab, open the :guilabel:`Volumes` tab and
   click :guilabel:`Volumes` category.

#. Click :guilabel:`Create Volume`.

   In the dialog box that opens, enter or select the following values.

   :guilabel:`Volume Name`: Specify a name for the volume.

   :guilabel:`Description`: Optionally, provide a brief description for the
   volume.

   :guilabel:`Volume Source`: Select one of the following options:

   * No source, empty volume: Creates an empty volume. An empty volume does
     not contain a file system or a partition table.

   * Snapshot: If you choose this option, a new field for
     :guilabel:`Use snapshot as a source` displays. You can select the
     snapshot from the list.

   * Image: If you choose this option, a new field for :guilabel:`Use image
     as a source` displays. You can select the image from the list.

   * Volume: If you choose this option, a new field for
     :guilabel:`Use volume as a source` displays. You can select the volume
     from the list. Options to use a snapshot or a volume as the source for a
     volume are displayed only if there are existing snapshots or volumes.

   :guilabel:`Type`: Leave this field blank.

   :guilabel:`Size (GB)`: The size of the volume in gibibytes (GiB).

   :guilabel:`Availability Zone`: Select the Availability Zone from the list.
   By default, this value is set to the availability zone given by the cloud
   provider (for example, ``us-west`` or ``apac-south``). For some cases,
   it could be ``nova``.

#. Click :guilabel:`Create Volume`.

The dashboard shows the volume on the :guilabel:`Volumes` tab.

.. _attach_a_volume_to_an_instance_dash:

Attach a volume to an instance
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

After you create one or more volumes, you can attach them to instances.
You can attach a volume to one instance at a time.

#. Log in to the dashboard.

#. Select the appropriate project from the drop down menu at the top left.

#. On the :guilabel:`Project` tab, open the :guilabel:`Volumes` tab and
   click :guilabel:`Volumes` category.

#. Select the volume to add to an instance and click
   :guilabel:`Manage Attachments`.

#. In the :guilabel:`Manage Volume Attachments` dialog box, select an instance.

#. Enter the name of the device from which the volume is accessible by
   the instance.

   .. note::

      The actual device name might differ from the volume name because
      of hypervisor settings.

#. Click :guilabel:`Attach Volume`.

   The dashboard shows the instance to which the volume is now attached
   and the device name.

You can view the status of a volume in the Volumes tab of the dashboard.
The volume is either Available or In-Use.

Now you can log in to the instance and mount, format, and use the disk.

Detach a volume from an instance
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

#. Log in to the dashboard.

#. Select the appropriate project from the drop down menu at the top left.

#. On the :guilabel:`Project` tab, open the :guilabel:`Volumes` tab and
   click the :guilabel:`Volumes` category.

#. Select the volume and click :guilabel:`Manage Attachments`.

#. Click :guilabel:`Detach Volume` and confirm your changes.

A message indicates whether the action was successful.

Create a snapshot from a volume
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

#. Log in to the dashboard.

#. Select the appropriate project from the drop down menu at the top left.

#. On the :guilabel:`Project` tab, open the :guilabel:`Volumes` tab and
   click :guilabel:`Volumes` category.

#. Select a volume from which to create a snapshot.

#. In the :guilabel:`Actions` column, click :guilabel:`Create Snapshot`.

#. In the dialog box that opens, enter a snapshot name and a brief
   description.

#. Confirm your changes.

   The dashboard shows the new volume snapshot in Volume Snapshots tab.

Edit a volume
~~~~~~~~~~~~~

#. Log in to the dashboard.

#. Select the appropriate project from the drop down menu at the top left.

#. On the :guilabel:`Project` tab, open the :guilabel:`Volumes` tab and
   click :guilabel:`Volumes` category.

#. Select the volume that you want to edit.

#. In the :guilabel:`Actions` column, click :guilabel:`Edit Volume`.

#. In the :guilabel:`Edit Volume` dialog box, update the name and description
   of the volume.

#. Click :guilabel:`Edit Volume`.

   .. note::

      You can extend a volume by using the :guilabel:`Extend Volume`
      option available in the :guilabel:`More` dropdown list and entering the
      new value for volume size.

Delete a volume
~~~~~~~~~~~~~~~

When you delete an instance, the data in its attached volumes is not
deleted.

#. Log in to the dashboard.

#. Select the appropriate project from the drop down menu at the top left.

#. On the :guilabel:`Project` tab, open the :guilabel:`Volumes` tab and
   click :guilabel:`Volumes` category.

#. Select the check boxes for the volumes that you want to delete.

#. Click :guilabel:`Delete Volumes` and confirm your choice.

   A message indicates whether the action was successful.
