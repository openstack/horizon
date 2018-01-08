========================
Create and manage images
========================

As an administrative user, you can create and manage images
for the projects to which you belong. You can also create
and manage images for users in all projects to which you have
access.

To create and manage images in specified projects as an end
user, see the :doc:`upload and manage images with Dashboard in
OpenStack End User Guide </user/manage-images>`
and `manage images with CLI in OpenStack End User Guide
<https://docs.openstack.org/glance/latest/admin/manage-images.html>`_.

To create and manage images as an administrator for other
users, use the following procedures.

Create images
~~~~~~~~~~~~~

For details about image creation, see the `Virtual Machine Image
Guide <https://docs.openstack.org/image-guide/>`_.

#. Log in to the Dashboard and select the :guilabel:`admin` project
   from the drop-down list.
#. On the :guilabel:`Admin` tab, open the :guilabel:`Compute` tab
   and click the :guilabel:`Images` category. The images that you
   can administer for cloud users appear on this page.
#. Click :guilabel:`Create Image`, which opens the
   :guilabel:`Create An Image` window.

   .. figure:: figures/create_image.png

      **Figure Dashboard — Create Image**

#. In the :guilabel:`Create An Image` window, enter or select the
   following values:

   +-------------------------------+---------------------------------+
   | :guilabel:`Name`              | Enter a name for the image.     |
   +-------------------------------+---------------------------------+
   | :guilabel:`Description`       | Enter a brief description of    |
   |                               | the image.                      |
   +-------------------------------+---------------------------------+
   | :guilabel:`Image Source`      | Choose the image source from    |
   |                               | the dropdown list. Your choices |
   |                               | are :guilabel:`Image Location`  |
   |                               | and :guilabel:`Image File`.     |
   +-------------------------------+---------------------------------+
   | :guilabel:`Image File` or     | Based on your selection, there  |
   | :guilabel:`Image Location`    | is an :guilabel:`Image File` or |
   |                               | :guilabel:`Image Location`      |
   |                               | field. You can include the      |
   |                               | location URL or browse for the  |
   |                               | image file on your file system  |
   |                               | and add it.                     |
   +-------------------------------+---------------------------------+
   | :guilabel:`Format`            | Select the image format.        |
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
   | :guilabel:`Public`            | Select this option to make the  |
   |                               | image public to all users.      |
   +-------------------------------+---------------------------------+
   | :guilabel:`Protected`         | Select this option to ensure    |
   |                               | that only users with            |
   |                               | permissions can delete it.      |
   +-------------------------------+---------------------------------+

#. Click :guilabel:`Create Image`.

   The image is queued to be uploaded. It might take several minutes
   before the status changes from ``Queued`` to ``Active``.

Update images
~~~~~~~~~~~~~

#. Log in to the Dashboard and select the :guilabel:`admin` project from the
   drop-down list.
#. On the :guilabel:`Admin` tab, open the :guilabel:`Compute` tab
   and click the :guilabel:`Images` category.
#. Select the images that you want to edit. Click :guilabel:`Edit Image`.
#. In the :guilabel:`Edit Image` window, you can change the image name.

   Select the :guilabel:`Public` check box to make the image public.
   Clear this check box to make the image private. You cannot change
   the :guilabel:`Kernel ID`, :guilabel:`Ramdisk ID`, or
   :guilabel:`Architecture` attributes for an image.
#. Click :guilabel:`Edit Image`.

Delete images
~~~~~~~~~~~~~

#. Log in to the Dashboard and select the :guilabel:`admin` project from the
   drop-down list.
#. On the :guilabel:`Admin tab`, open the :guilabel:`Compute` tab
   and click the :guilabel:`Images` category.
#. Select the images that you want to delete.
#. Click :guilabel:`Delete Images`.
#. In the :guilabel:`Confirm Delete Images` window, click :guilabel:`Delete
   Images` to confirm the deletion.

   You cannot undo this action.
