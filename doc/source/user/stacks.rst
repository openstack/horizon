========================
Launch and manage stacks
========================

OpenStack Orchestration is a service that you can use to
orchestrate multiple composite cloud applications. This
service supports the use of both the Amazon Web Services (AWS)
CloudFormation template format through both a Query API that
is compatible with CloudFormation and the native OpenStack
Heat Orchestration Template (HOT) format through a REST API.

These flexible template languages enable application
developers to describe and automate the deployment of
infrastructure, services, and applications. The templates
enable creation of most OpenStack resource types, such as
instances, floating IP addresses, volumes, security groups,
and users. Once created, the resources are referred to as
stacks.

The template languages are described in the `Template Guide
<https://docs.openstack.org/heat/latest/template_guide/>`_.

Launch a stack
~~~~~~~~~~~~~~

#. Log in to the dashboard.
#. Select the appropriate project from the drop down menu at the top left.
#. On the :guilabel:`Project` tab, open the :guilabel:`Orchestration` tab and
   click :guilabel:`Stacks` category.
#. Click :guilabel:`Launch Stack`.
#. In the :guilabel:`Select Template` dialog box, specify the
   following values:

   +---------------------------------------+-------------------------------+
   | :guilabel:`Template Source`           | Choose the source of the      |
   |                                       | template from the list.       |
   +---------------------------------------+-------------------------------+
   | :guilabel:`Template URL/File/Data`    | Depending on the source that  |
   |                                       | you select, enter the URL,    |
   |                                       | browse to the file location,  |
   |                                       | or directly include the       |
   |                                       | template.                     |
   +---------------------------------------+-------------------------------+
   | :guilabel:`Environment Source`        | Choose the source of the      |
   |                                       | environment from the list.    |
   |                                       | The environment files contain |
   |                                       | additional settings for the   |
   |                                       | stack.                        |
   +---------------------------------------+-------------------------------+
   | :guilabel:`Environment File/Data`     | Depending on the source that  |
   |                                       | you select, browse to the     |
   |                                       | file location, directly       |
   |                                       | include the environment       |
   +---------------------------------------+-------------------------------+

#. Click :guilabel:`Next`.
#. In the :guilabel:`Launch Stack` dialog box, specify the
   following values:

   +---------------------------------+---------------------------------+
   | :guilabel:`Stack Name`          | Enter a name to identify        |
   |                                 | the stack.                      |
   +---------------------------------+---------------------------------+
   | :guilabel:`Creation Timeout`    | Specify the number of minutes   |
   | :guilabel:`(minutes)`           | that can elapse before the      |
   |                                 | launch of the stack times out.  |
   +---------------------------------+---------------------------------+
   | :guilabel:`Rollback On Failure` | Select this check box if you    |
   |                                 | want the service to roll back   |
   |                                 | changes if the stack fails to   |
   |                                 | launch.                         |
   +---------------------------------+---------------------------------+
   | :guilabel:`Password for user`   | Specify the password that       |
   | :guilabel:`"demo"`              | the default user uses when the  |
   |                                 | stack is created.               |
   +---------------------------------+---------------------------------+
   | :guilabel:`DBUsername`          | Specify the name of the         |
   |                                 | database user.                  |
   +---------------------------------+---------------------------------+
   | :guilabel:`LinuxDistribution`   | Specify the Linux distribution  |
   |                                 | that is used in the stack.      |
   +---------------------------------+---------------------------------+
   | :guilabel:`DBRootPassword`      | Specify the root password for   |
   |                                 | the database.                   |
   +---------------------------------+---------------------------------+
   | :guilabel:`KeyName`             | Specify the name of the key pair|
   |                                 | to use to log in to the stack.  |
   +---------------------------------+---------------------------------+
   | :guilabel:`DBName`              | Specify the name of the         |
   |                                 | database.                       |
   +---------------------------------+---------------------------------+
   | :guilabel:`DBPassword`          | Specify the password of the     |
   |                                 | database.                       |
   +---------------------------------+---------------------------------+
   | :guilabel:`InstanceType`        | Specify the flavor for the      |
   |                                 | instance.                       |
   +---------------------------------+---------------------------------+

#. Click :guilabel:`Launch` to create a stack. The :guilabel:`Stacks`
   tab shows the stack.

After the stack is created, click on the stack name to see the
following details:

Topology
  The topology of the stack.

Overview
  The parameters and details of the stack.

Resources
  The resources used by the stack.

Events
  The events related to the stack.

Template
  The template for the stack.

Manage a stack
~~~~~~~~~~~~~~

#. Log in to the dashboard.
#. Select the appropriate project from the drop down menu at the top left.
#. On the :guilabel:`Project` tab, open the :guilabel:`Orchestration` tab and
   click :guilabel:`Stacks` category.
#. Select the stack that you want to update.
#. Click :guilabel:`Change Stack Template`.
#. In the :guilabel:`Select Template` dialog box, select the
   new template source or environment source.
#. Click :guilabel:`Next`.

   The :guilabel:`Update Stack Parameters` window appears.
#. Enter new values for any parameters that you want to update.
#. Click :guilabel:`Update`.

Delete a stack
~~~~~~~~~~~~~~

When you delete a stack, you cannot undo this action.

#. Log in to the dashboard.
#. Select the appropriate project from the drop down menu at the top left.
#. On the :guilabel:`Project` tab, open the :guilabel:`Orchestration` tab and
   click :guilabel:`Stacks` category.
#. Select the stack that you want to delete.
#. Click :guilabel:`Delete Stack`.
#. In the confirmation dialog box, click :guilabel:`Delete Stack`
   to confirm the deletion.
