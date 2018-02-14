=============================
Manage shares and share types
=============================

Shares are file storage that instances can access. Users can
allow or deny a running instance to have access to a share at any time.
For information about using the Dashboard to create and manage shares as
an end user, see the
:doc:`OpenStack End User Guide </user/manage-shares>`.

As an administrative user, you can manage shares and share types for users
in various projects. You can create and delete share types, and view
or delete shares.

.. _create-a-share-type:

Create a share type
~~~~~~~~~~~~~~~~~~~

#. Log in to the Dashboard and choose the :guilabel:`admin`
   project from the drop-down list.

#. On the :guilabel:`Admin` tab, open the :guilabel:`System` tab
   and click the :guilabel:`Shares` category.

#. Click the :guilabel:`Share Types` tab, and click
   :guilabel:`Create Share Type` button. In the
   :guilabel:`Create Share Type` window, enter or select the
   following values.

   :guilabel:`Name`: Enter a name for the share type.

   :guilabel:`Driver handles share servers`: Choose True or False

   :guilabel:`Extra specs`: To add extra specs, use key=value.

#. Click :guilabel:`Create Share Type` button to confirm your changes.

.. note::

   A message indicates whether the action succeeded.

Update share type
~~~~~~~~~~~~~~~~~

#. Log in to the Dashboard and choose the :guilabel:`admin` project from
   the drop-down list.

#. On the :guilabel:`Admin` tab, open the :guilabel:`System` tab
   and click the :guilabel:`Shares` category.

#. Click the :guilabel:`Share Types` tab, select the share type
   that you want to update.

#. Select :guilabel:`Update Share Type` from Actions.

#. In the :guilabel:`Update Share Type` window, update extra specs.

   :guilabel:`Extra specs`: To add extra specs, use key=value.
   To unset extra specs, use key.

#. Click :guilabel:`Update Share Type` button to confirm your changes.

.. note::

   A message indicates whether the action succeeded.

Delete share types
~~~~~~~~~~~~~~~~~~

When you delete a share type, shares of that type are not deleted.

#. Log in to the Dashboard and choose the :guilabel:`admin` project from
   the drop-down list.

#. On the :guilabel:`Admin` tab, open the :guilabel:`System` tab
   and click the :guilabel:`Shares` category.

#. Click the :guilabel:`Share Types` tab, select the share type
   or types that you want to delete.

#. Click :guilabel:`Delete Share Types` button.

#. In the :guilabel:`Confirm Delete Share Types` window, click the
   :guilabel:`Delete Share Types` button to confirm the action.

.. note::

   A message indicates whether the action succeeded.

Delete shares
~~~~~~~~~~~~~

#. Log in to the Dashboard and choose the :guilabel:`admin` project
   from the drop-down list.

#. On the :guilabel:`Admin` tab, open the :guilabel:`System` tab
   and click the :guilabel:`Shares` category.

#. Select the share or shares that you want to delete.

#. Click :guilabel:`Delete Shares` button.

#. In the :guilabel:`Confirm Delete Shares` window, click the
   :guilabel:`Delete Shares` button to confirm the action.

.. note::

   A message indicates whether the action succeeded.

Delete share server
~~~~~~~~~~~~~~~~~~~

#. Log in to the Dashboard and choose the :guilabel:`admin` project
   from the drop-down list.

#. On the :guilabel:`Admin` tab, open the :guilabel:`System` tab
   and click the :guilabel:`Share Servers` category.

#. Select the share that you want to delete.

#. Click :guilabel:`Delete Share Server` button.

#. In the :guilabel:`Confirm Delete Share Server` window, click the
   :guilabel:`Delete Share Server` button to confirm the action.

.. note::

   A message indicates whether the action succeeded.

Delete share networks
~~~~~~~~~~~~~~~~~~~~~

#. Log in to the Dashboard and choose the :guilabel:`admin` project
   from the drop-down list.

#. On the :guilabel:`Admin` tab, open the :guilabel:`System` tab
   and click the :guilabel:`Share Networks` category.

#. Select the share network or share networks that you want to delete.

#. Click :guilabel:`Delete Share Networks` button.

#. In the :guilabel:`Confirm Delete Share Networks` window, click the
   :guilabel:`Delete Share Networks` button to confirm the action.

.. note::

   A message indicates whether the action succeeded.
