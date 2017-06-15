Manage projects and users
=========================

OpenStack administrators can create projects, and create accounts for new users
using the OpenStack Dasboard. Projects own specific resources in your
OpenStack environment. You can associate users with roles, projects, or both.

Add a new project
~~~~~~~~~~~~~~~~~

#. Log into the OpenStack Dashboard as the Admin user.
#. Click on the :guilabel:`Identity` label on the left column, and click
   :guilabel:`Projects`.
#. Select the :guilabel:`Create Project` push button.
   The :guilabel:`Create Project` window will open.
#. Enter the Project name and description. Leave the :guilabel:`Domain ID`
   field set at *default*.
#. Click :guilabel:`Create Project`.

.. note::

   Your new project will appear in the list of projects displayed under the
   :guilabel:`Projects` page of the dashboard. Projects are listed in
   alphabetical order, and you can check on the **Project ID**, **Domain
   name**, and status of the project in this section.

Delete a project
~~~~~~~~~~~~~~~~

#. Log into the OpenStack Dashboard as the Admin user.
#. Click on the :guilabel:`Identity` label on the left column, and click
   :guilabel:`Projects`.
#. Select the checkbox to the left of the project you would like to delete.
#. Click on the :guilabel:`Delete Projects` push button.

Update a project
~~~~~~~~~~~~~~~~

#. Log into the OpenStack Dashboard as the Admin user.
#. Click on the :guilabel:`Identity` label on the left column, and click
   :guilabel:`Projects`.
#. Locate the project you wish to update, and under the :guilabel:`Actions`
   column click on the drop down arrow next to the :guilabel:`Manage Members`
   push button. The :guilabel:`Update Project` window will open.
#. Update the name of the project, enable the project, or disable the project
   as needed.

Add a new user
~~~~~~~~~~~~~~

#. Log into the OpenStack Dashboard as the Admin user.
#. Click on the :guilabel:`Identity` label on the left column, and click
   :guilabel:`Users`.
#. Click :guilabel:`Create User`.
#. Enter a :guilabel:`Domain Name`, the :guilabel:`Username`, and a
   :guilabel:`password` for the new user. Enter an email for the new user,
   and specify which :guilabel:`Primary Project` they belong to. Leave the
   :guilabel:`Domain ID` field set at *default*. You can also enter a
   decription for the new user.
#. Click the :guilabel:`Create User` push button.

.. note::

   The new user will then appear in the list of projects displayed under
   the :guilabel:`Users` page of the dashboard. You can check on the
   **User Name**, **User ID**, **Domain name**, and the User status in this
   section.

Delete a new user
~~~~~~~~~~~~~~~~~

#. Log into the OpenStack Dashboard as the Admin user.
#. Click on the :guilabel:`Identity` label on the left column, and click
   :guilabel:`Users`.
#. Select the checkbox to the left of the user you would like to delete.
#. Click on the :guilabel:`Delete Users` push button.

Update a user
~~~~~~~~~~~~~

#. Log into the OpenStack Dashboard as the Admin user.
#. Click on the :guilabel:`Identity` label on the left column, and click
   :guilabel:`Users`.
#. Locate the User you would like to update, and select the :guilabel:`Edit`
   push button under the :guilabel:`Actions` column.
#. Adjust the :guilabel:`Domain Name`, :guilabel:`User Name`,
   :guilabel:`Description`, :guilabel:`Email`, and :guilabel:`Primary Project`.

Enable or disable a user
------------------------

#. Log into the OpenStack Dashboard as the Admin user.
#. Click on the :guilabel:`Identity` label on the left column, and click
   :guilabel:`Users`.
#. Locate the User you would like to update, and select the arrow to the right
   of the :guilabel:`Edit` push button. This will open a drop down menu.
#. Select :guilabel:`Disable User`.

.. note::

   To reactivate a disabled user, select :guilabel:`Enable User` under
   the drop down menu.
