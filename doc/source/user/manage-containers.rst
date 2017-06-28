===================================
Create and manage object containers
===================================

OpenStack Object Storage (swift) is used for redundant, scalable data storage
using clusters of standardized servers to store petabytes of accessible data.
It is a long-term storage system for large amounts of static data which can be
retrieved and updated.

OpenStack Object Storage provides a distributed, API-accessible storage
platform that can be integrated directly into an application or used to
store any type of file, including VM images, backups, archives, or media
files. In the OpenStack dashboard, you can only manage containers and
objects.

In OpenStack Object Storage, containers provide storage for objects in a
manner similar to a Windows folder or Linux file directory, though they
cannot be nested. An object in OpenStack consists of the file to be
stored in the container and any accompanying metadata.

Create a container
~~~~~~~~~~~~~~~~~~

#. Log in to the dashboard.

#. Select the appropriate project from the drop down menu at the top left.

#. On the :guilabel:`Project` tab, open the :guilabel:`Object Store` tab and
   click :guilabel:`Containers` category.

#. Click :guilabel:`Container`.

#. In the :guilabel:`Create Container` dialog box, enter a name for the
   container, and then click :guilabel:`Create`.

You have successfully created a container.

.. note::

   To delete a container, click the :guilabel:`More` button and select
   :guilabel:`Delete Container`.

Upload an object
~~~~~~~~~~~~~~~~

#. Log in to the dashboard.

#. Select the appropriate project from the drop down menu at the top left.

#. On the :guilabel:`Project` tab, open the :guilabel:`Object Store` tab and
   click :guilabel:`Containers` category.

#. Select the container in which you want to store your object.

#. Click the :guilabel:`Upload File` icon.

   The :guilabel:`Upload File To Container: <name>` dialog box
   appears.
   ``<name>`` is the name of the container to which you are uploading
   the object.

#. Enter a name for the object.

#. Browse to and select the file that you want to upload.

#. Click :guilabel:`Upload File`.

You have successfully uploaded an object to the container.

.. note::

   To delete an object, click the :guilabel:`More button` and select
   :guilabel:`Delete Object`.

Manage an object
~~~~~~~~~~~~~~~~

**To edit an object**

#. Log in to the dashboard.

#. Select the appropriate project from the drop down menu at the top left.

#. On the :guilabel:`Project` tab, open the :guilabel:`Object Store` tab and
   click :guilabel:`Containers` category.

#. Select the container in which you want to store your object.

#. Click the menu button and choose :guilabel:`Edit` from the dropdown list.

   The :guilabel:`Edit Object` dialog box is displayed.

#. Browse to and select the file that you want to upload.

#. Click :guilabel:`Update Object`.

.. note::

   To delete an object, click the menu button and select
   :guilabel:`Delete Object`.

**To copy an object from one container to another**

#. Log in to the dashboard.

#. Select the appropriate project from the drop down menu at the top left.

#. On the :guilabel:`Project` tab, open the :guilabel:`Object Store` tab and
   click :guilabel:`Containers` category.

#. Select the container in which you want to store your object.

#. Click the menu button and choose :guilabel:`Copy` from the dropdown list.

#. In the :guilabel:`Copy Object` launch dialog box, enter the following
   values:

   * :guilabel:`Destination Container`: Choose the destination container from
     the list.
   * :guilabel:`Path`: Specify a path in which the new copy should be stored
     inside of the selected container.
   * :guilabel:`Destination object name`: Enter a name for the object in the
     new container.

#. Click :guilabel:`Copy Object`.

**To create a metadata-only object without a file**

You can create a new object in container without a file available and
can upload the file later when it is ready. This temporary object acts a
place-holder for a new object, and enables the user to share object
metadata and URL info in advance.

#. Log in to the dashboard.

#. Select the appropriate project from the drop down menu at the top left.

#. On the :guilabel:`Project` tab, open the :guilabel:`Object Store` tab and
   click :guilabel:`Containers` category.

#. Select the container in which you want to store your object.

#. Click :guilabel:`Upload Object`.

   The :guilabel:`Upload Object To Container`: ``<name>`` dialog box is
   displayed.

   ``<name>`` is the name of the container to which you are uploading
   the object.

#. Enter a name for the object.

#. Click :guilabel:`Update Object`.

**To create a pseudo-folder**

Pseudo-folders are similar to folders in your desktop operating system.
They are virtual collections defined by a common prefix on the object's
name.

#. Log in to the dashboard.

#. Select the appropriate project from the drop down menu at the top left.

#. On the :guilabel:`Project` tab, open the :guilabel:`Object Store` tab and
   click :guilabel:`Containers` category.

#. Select the container in which you want to store your object.

#. Click :guilabel:`Create Pseudo-folder`.

   The :guilabel:`Create Pseudo-Folder in Container` ``<name>`` dialog box
   is displayed. ``<name>`` is the name of the container to which you
   are uploading the object.

#. Enter a name for the pseudo-folder.

   A slash (/) character is used as the delimiter for pseudo-folders in
   Object Storage.

#. Click :guilabel:`Create`.
