=======================
Create and manage roles
=======================

A role is a personality that a user assumes to perform a specific set
of operations. A role includes a set of rights and privileges. A user
assumes that role inherits those rights and privileges.

.. note::

   OpenStack Identity service defines a user's role on a
   project, but it is completely up to the individual service
   to define what that role means. This is referred to as the
   service's policy. To get details about what the privileges
   for each role are, refer to the ``policy.json`` file
   available for each service in the
   ``/etc/SERVICE/policy.json`` file. For example, the
   policy defined for OpenStack Identity service is defined
   in the ``/etc/keystone/policy.json`` file.

Create a role
~~~~~~~~~~~~~

#. Log in to the dashboard and select the :guilabel:`admin` project from the
   drop-down list.
#. On the :guilabel:`Identity` tab, click the :guilabel:`Roles` category.
#. Click the :guilabel:`Create Role` button.

   In the :guilabel:`Create Role` window, enter a name for the role.
#. Click the :guilabel:`Create Role` button to confirm your changes.

Edit a role
~~~~~~~~~~~

#. Log in to the dashboard and select the :guilabel:`Identity` project from the
   drop-down list.
#. On the :guilabel:`Identity` tab, click the :guilabel:`Roles` category.
#. Click the :guilabel:`Edit` button.

   In the :guilabel:`Update Role` window, enter a new name for the role.
#. Click the :guilabel:`Update Role` button to confirm your changes.

.. note::

   Using the dashboard, you can edit only the name assigned to
   a role.

Delete a role
~~~~~~~~~~~~~

#. Log in to the dashboard and select the :guilabel:`Identity` project from the
   drop-down list.
#. On the :guilabel:`Identity` tab, click the :guilabel:`Roles` category.
#. Select the role you want to delete and click the :guilabel:`Delete
   Roles` button.
#. In the :guilabel:`Confirm Delete Roles` window, click :guilabel:`Delete
   Roles` to confirm the deletion.

   You cannot undo this action.
