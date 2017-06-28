=========================
Create and manage shares
=========================

Shares are file storage that you provide access to instances. You can allow
access to a share to a running instance or deny access to a share and allow
access to it to another instance at any time. You can also delete a share.
You can create snapshot from a share if the driver supports it. Only
administrative users can create share types.

Create a share
~~~~~~~~~~~~~~~

#. Log in to the dashboard, choose a project, and click :guilabel:`Shares`.

#. Click :guilabel:`Create Share`.

   In the dialog box that opens, enter or select the following values.

   :guilabel:`Share Name`: Specify a name for the share.

   :guilabel:`Description`: Optionally, provide a brief description for the
   share.

   :guilabel:`Share Type`: Choose a share type.

   :guilabel:`Size (GB)`: The size of the share in gibibytes (GiB).

   :guilabel:`Share Protocol`: Select NFS, CIFS, GlusterFS, or HDFS.

   :guilabel:`Share Network`: Choose a share network.

   :guilabel:`Metadata`: Enter metadata for the share creation if needed.

#. Click :guilabel:`Create Share`.

The dashboard shows the share on the :guilabel:`Shares` tab.

Delete a share
~~~~~~~~~~~~~~~

#. Log in to the dashboard, choose a project, and click :guilabel:`Shares`.

#. Select the check boxes for the shares that you want to delete.

#. Click :guilabel:`Delete Shares` and confirm your choice.

   A message indicates whether the action was successful.

Allow access
~~~~~~~~~~~~

#. Log in to the dashboard, choose a project, and click :guilabel:`Shares`.

#. Go to the share that you want to allow access and choose
   :guilabel:`Manage Rules` from Actions.

#. Click :guilabel:`Add rule`.

   :guilabel:`Access Type`: Choose ip, user, or cert.

   :guilabel:`Access Level`: Choose read-write or read-only.

   :guilabel:`Access To`: Fill in Access To field.

#. Click :guilabel:`Add Rule`.

   A message indicates whether the action was successful.

Deny access
~~~~~~~~~~~

#. Log in to the dashboard, choose a project, and click :guilabel:`Shares`.

#. Go to the share that you want to deny access and choose
   :guilabel:`Manage Rules` from Actions.

#. Choose the rule you want to delete.

#. Click :guilabel:`Delete rule` and confirm your choice.

   A message indicates whether the action was successful.

Edit share metadata
~~~~~~~~~~~~~~~~~~~

#. Log in to the dashboard, choose a project, and click :guilabel:`Shares`.

#. Go to the share that you want to edit and choose
   :guilabel:`Edit Share Metadata` from Actions.

#. :guilabel:`Metadata`: To add share metadata, use key=value. To unset
   metadata, use key.

#. Click :guilabel:`Edit Share Metadata`.

   A message indicates whether the action was successful.

Edit share
~~~~~~~~~~

#. Log in to the dashboard, choose a project, and click :guilabel:`Shares`.

#. Go to the share that you want to edit and choose :guilabel:`Edit Share` from
   Actions.

#. :guilabel:`Share Name`: Enter a new share name.

#. :guilabel:`Description`: Enter a new description.

#. Click :guilabel:`Edit Share`.

   A message indicates whether the action was successful.

Extend share
~~~~~~~~~~~~

#. Log in to the dashboard, choose a project, and click :guilabel:`Shares`.

#. Go to the share that you want to edit and choose :guilabel:`Extend Share`
   from Actions.

#. :guilabel:`New Size (GB)`: Enter new size.

#. Click :guilabel:`Extend Share`.

   A message indicates whether the action was successful.

Create share network
~~~~~~~~~~~~~~~~~~~~

#. Log in to the dashboard, choose a project, click :guilabel:`Shares`,
   and click :guilabel:`Share Networks`.

#. Click :guilabel:`Create Share Network`.

   In the dialog box that opens, enter or select the following values.

   :guilabel:`Name`: Specify a name for the share network.

   :guilabel:`Description`: Optionally, provide a brief description for the
   share network.

   :guilabel:`Neutron Net`: Choose a neutron network.

   :guilabel:`Neutron Subnet`: Choose a neutron subnet.

#. Click :guilabel:`Create Share Network`.

The dashboard shows the share network on the :guilabel:`Share Networks` tab.

Delete a share network
~~~~~~~~~~~~~~~~~~~~~~

#. Log in to the dashboard, choose a project, click :guilabel:`Shares`, and
   click :guilabel:`Share Networks`.

#. Select the check boxes for the share networks that you want to delete.

#. Click :guilabel:`Delete Share Networks` and confirm your choice.

   A message indicates whether the action was successful.

Edit share network
~~~~~~~~~~~~~~~~~~

#. Log in to the dashboard, choose a project, click :guilabel:`Shares`, and
   click :guilabel:`Share Networks`.

#. Go to the share network that you want to edit and choose
   :guilabel:`Edit Share Network` from Actions.

#. :guilabel:`Name`: Enter a new share network name.

#. :guilabel:`Description`: Enter a new description.

#. Click :guilabel:`Edit Share Network`.

   A message indicates whether the action was successful.

Create security service
~~~~~~~~~~~~~~~~~~~~~~~

#. Log in to the dashboard, choose a project, click :guilabel:`Shares`,
   and click :guilabel:`Security Services`.

#. Click :guilabel:`Create Security Service`.

   In the dialog box that opens, enter or select the following values.

   :guilabel:`Name`: Specify a name for the security service.

   :guilabel:`DNS IP`: Enter the DNS IP address.

   :guilabel:`Server`: Enter the server name.

   :guilabel:`Domain`: Enter the domain name.

   :guilabel:`User`: Enter the user name.

   :guilabel:`Password`: Enter the password.

   :guilabel:`Confirm Password`: Enter the password again to confirm.

   :guilabel:`Type`: Choose the type from Active Directory, LDAP, or Kerberos.

   :guilabel:`Description`: Optionally, provide a brief description for the
   security service.

#. Click :guilabel:`Create Security Service`.

The dashboard shows the security service on the :guilabel:`Security Services`
tab.

Delete a security service
~~~~~~~~~~~~~~~~~~~~~~~~~

#. Log in to the dashboard, choose a project, click :guilabel:`Shares`, and
   click :guilabel:`Security Services`.

#. Select the check boxes for the security services that you want to delete.

#. Click :guilabel:`Delete Security Services` and confirm your choice.

   A message indicates whether the action was successful.

Edit security service
~~~~~~~~~~~~~~~~~~~~~

#. Log in to the dashboard, choose a project, click :guilabel:`Shares`,
   and click :guilabel:`Security Services`.

#. Go to the security service that you want to edit and choose
   :guilabel:`Edit Security Service` from Actions.

#. :guilabel:`Name`: Enter a new security service name.

#. :guilabel:`Description`: Enter a new description.

#. Click :guilabel:`Edit Security Service`.

   A message indicates whether the action was successful.
