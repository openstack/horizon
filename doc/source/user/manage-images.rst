========================
Upload and manage images
========================

A virtual machine image, referred to in this document simply
as an image, is a single file that contains a virtual disk that
has a bootable operating system installed on it. Images are used
to create virtual machine instances within the cloud. For information
about creating image files, see the `OpenStack Virtual Machine
Image Guide <https://docs.openstack.org/image-guide/>`_.

Depending on your role, you may have permission to upload and manage
virtual machine images. Operators might restrict the upload and
management of images to cloud administrators or operators only. If you
have the appropriate privileges, you can use the dashboard to upload and
manage images in the admin project.

.. note::

   You can also use the :command:`openstack` and :command:`glance`
   command-line clients or the Image service to manage images.

Upload an image
~~~~~~~~~~~~~~~

Follow this procedure to upload an image to a project:

#. Log in to the dashboard.

#. Select the appropriate project from the drop down menu at the top left.

#. On the :guilabel:`Project` tab, open the :guilabel:`Compute` tab and
   click :guilabel:`Images` category.

#. Click :guilabel:`Create Image`.

   The :guilabel:`Create An Image` dialog box appears.

   .. figure:: figures/create_image.png

      **Dashboard — Create Image**

#. Enter the following values:

   +-------------------------------+---------------------------------+
   | :guilabel:`Image Name`        | Enter a name for the image.     |
   +-------------------------------+---------------------------------+
   | :guilabel:`Image Description` | Enter a brief description of    |
   |                               | the image.                      |
   +-------------------------------+---------------------------------+
   | :guilabel:`Image Source`      | Choose the image source from    |
   |                               | the dropdown list. Your choices |
   |                               | are :guilabel:`Image Location`  |
   |                               | and :guilabel:`Image File`.     |
   +-------------------------------+---------------------------------+
   | :guilabel:`Image File` or     | Based on your selection for     |
   | :guilabel:`Image Location`    | :guilabel:`Image Source`, you   |
   |                               | either enter the location URL   |
   |                               | of the image in the             |
   |                               | :guilabel:`Image Location`      |
   |                               | field, or browse for the image  |
   |                               | file on your file  system and   |
   |                               | add it.                         |
   +-------------------------------+---------------------------------+
   | :guilabel:`Format`            | Select the image format (for    |
   |                               | example, QCOW2) for the image.  |
   +-------------------------------+---------------------------------+
   | :guilabel:`Architecture`      | Specify the architecture. For   |
   |                               | example, ``i386`` for a 32-bit  |
   |                               | architecture or ``x86_64`` for  |
   |                               | a 64-bit architecture.          |
   +-------------------------------+---------------------------------+
   | :guilabel:`Minimum Disk (GB)` | Leave this field empty.         |
   +-------------------------------+---------------------------------+
   | :guilabel:`Minimum RAM (MB)`  | Leave this field empty.         |
   +-------------------------------+---------------------------------+
   | :guilabel:`Copy Data`         | Specify this option to copy     |
   |                               | image data to the Image service.|
   +-------------------------------+---------------------------------+
   | :guilabel:`Visibility`        | The access permission for the   |
   |                               | image.                          |
   |                               | ``Public`` or ``Private``.      |
   +-------------------------------+---------------------------------+
   | :guilabel:`Protected`         | Select this check box to ensure |
   |                               | that only users with            |
   |                               | permissions can delete the      |
   |                               | image. ``Yes`` or ``No``.       |
   +-------------------------------+---------------------------------+
   | :guilabel:`Image Metadata`    | Specify this option to add      |
   |                               | resource metadata. The glance   |
   |                               | Metadata Catalog provides a list|
   |                               | of metadata image definitions.  |
   |                               | (Note: Not all cloud providers  |
   |                               | enable this feature.)           |
   +-------------------------------+---------------------------------+

#. Click :guilabel:`Create Image`.

   The image is queued to be uploaded. It might take some time before
   the status changes from Queued to Active.

Update an image
~~~~~~~~~~~~~~~

Follow this procedure to update an existing image.

#. Log in to the dashboard.

#. Select the appropriate project from the drop down menu at the top left.

#. Select the image that you want to edit.

#. In the :guilabel:`Actions` column, click the menu button and then
   select :guilabel:`Edit Image` from the list.

#. In the :guilabel:`Edit Image` dialog box, you can perform various
   actions. For example:

   *  Change the name of the image.
   *  Change the description of the image.
   *  Change the format of the image.
   *  Change the minimum disk of the image.
   *  Change the minimum RAM  of the image.
   *  Select the :guilabel:`Public` button to make the image public.
   *  Clear the :guilabel:`Private` button to make the image private.
   *  Change the metadata of the image.

#. Click :guilabel:`Edit Image`.

Delete an image
~~~~~~~~~~~~~~~

Deletion of images is permanent and **cannot** be reversed. Only users
with the appropriate permissions can delete images.

#. Log in to the dashboard.

#. Select the appropriate project from the drop down menu at the top left.

#. On the :guilabel:`Project` tab, open the :guilabel:`Compute` tab and
   click :guilabel:`Images` category.

#. Select the images that you want to delete.

#. Click :guilabel:`Delete Images`.

#. In the :guilabel:`Confirm Delete Images` dialog box, click
   :guilabel:`Delete Images` to confirm the deletion.
