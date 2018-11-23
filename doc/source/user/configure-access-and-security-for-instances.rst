===========================================
Configure access and security for instances
===========================================

Before you launch an instance, you should add security group rules to
enable users to ping and use SSH to connect to the instance. Security
groups are sets of IP filter rules that define networking access and are
applied to all instances within a project. To do so, you either add
rules to the default security group :ref:`security_groups_add_rule`
or add a new security group with rules.

Key pairs are SSH credentials that are injected into an instance when it
is launched. To use key pair injection, the image that the instance is
based on must contain the ``cloud-init`` package. Each project should
have at least one key pair. For more information, see the section
:ref:`keypair_add`.

If you have generated a key pair with an external tool, you can import
it into OpenStack. The key pair can be used for multiple instances that
belong to a project. For more information, see the section
:ref:`dashboard_import_keypair`.

.. note::

   A key pair belongs to an individual user, not to a project.
   To share a key pair across multiple users, each user
   needs to import that key pair.

When an instance is created in OpenStack, it is automatically assigned a
fixed IP address in the network to which the instance is assigned. This
IP address is permanently associated with the instance until the
instance is terminated. However, in addition to the fixed IP address, a
floating IP address can also be attached to an instance. Unlike fixed IP
addresses, floating IP addresses are able to have their associations
modified at any time, regardless of the state of the instances involved.

.. _security_groups_add_rule:

Add a rule to the default security group
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This procedure enables SSH and ICMP (ping) access to instances. The
rules apply to all instances within a given project, and should be set
for every project unless there is a reason to prohibit SSH or ICMP
access to the instances.

This procedure can be adjusted as necessary to add additional security
group rules to a project, if your cloud requires them.

.. note::

   When adding a rule, you must specify the protocol used with the
   destination port or source port.

#. Log in to the dashboard.

#. Select the appropriate project from the drop down menu at the top left.

#. On the :guilabel:`Project` tab, open the :guilabel:`Network` tab. The
   :guilabel:`Security Groups` tab shows the security groups that are
   available for this project.

#. Select the default security group and click :guilabel:`Manage Rules`.

#. To allow SSH access, click :guilabel:`Add Rule`.

#. In the :guilabel:`Add Rule` dialog box, enter the following values:

   * **Rule**: ``SSH``
   * **Remote**: ``CIDR``
   * **CIDR**: ``0.0.0.0/0``

   .. note::

      To accept requests from a particular range of IP
      addresses, specify the IP address block in the
      :guilabel:`CIDR` box.

#. Click :guilabel:`Add`.

   Instances will now have SSH port 22 open for requests from any IP
   address.

#. To add an ICMP rule, click :guilabel:`Add Rule`.

#. In the :guilabel:`Add Rule` dialog box, enter the following values:

   * **Rule**: ``All ICMP``
   * **Direction**: ``Ingress``
   * **Remote**: ``CIDR``
   * **CIDR**: ``0.0.0.0/0``

#. Click :guilabel:`Add`.

   Instances will now accept all incoming ICMP packets.

.. _keypair_add:

Add a key pair
~~~~~~~~~~~~~~

Create at least one key pair for each project.


#. Log in to the dashboard.

#. Select the appropriate project from the drop down menu at the top left.

#. On the :guilabel:`Project` tab, open the :guilabel:`Compute` tab.

#. Click the :guilabel:`Key Pairs` tab, which shows the key pairs that
   are available for this project.

#. Click :guilabel:`Create Key Pair`.

#. In the :guilabel:`Create Key Pair` dialog box, enter a name for your
   key pair, and click :guilabel:`Create Key Pair`.

#. The private key will be downloaded automatically.

#. To change its permissions so that only you can read and write to the
   file, run the following command:

   .. code-block:: console

      $ chmod 0600 yourPrivateKey.pem

   .. note::

      If you are using the Dashboard from a Windows computer, use PuTTYgen
      to load the ``*.pem`` file and convert and save it as ``*.ppk``. For
      more information see the `WinSCP web page for
      PuTTYgen <https://winscp.net/eng/docs/ui_puttygen>`__.

#. To make the key pair known to SSH, run the :command:`ssh-add` command.

   .. code-block:: console

      $ ssh-add yourPrivateKey.pem

.. _dashboard_import_keypair:

Import a key pair
~~~~~~~~~~~~~~~~~

#. Log in to the dashboard.

#. Select the appropriate project from the drop down menu at the top left.

#. On the :guilabel:`Project` tab, open the :guilabel:`Compute` tab.

#. Click the :guilabel:`Key Pairs` tab, which shows the key pairs that
   are available for this project.

#. Click :guilabel:`Import Key Pair`.

#. In the :guilabel:`Import Key Pair` dialog box, enter the name of your
   key pair, copy the public key into the :guilabel:`Public Key` box,
   and then click :guilabel:`Import Key Pair`.

The Compute database registers the public key of the key pair.

The Dashboard lists the key pair on the :guilabel:`Key Pairs` tab.

Allocate a floating IP address to an instance
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

When an instance is created in OpenStack, it is automatically assigned a
fixed IP address in the network to which the instance is assigned. This
IP address is permanently associated with the instance until the
instance is terminated.

However, in addition to the fixed IP address, a floating IP address can
also be attached to an instance. Unlike fixed IP addresses, floating IP
addresses can have their associations modified at any time, regardless
of the state of the instances involved. This procedure details the
reservation of a floating IP address from an existing pool of addresses
and the association of that address with a specific instance.


#. Log in to the dashboard.

#. Select the appropriate project from the drop down menu at the top left.

#. On the :guilabel:`Project` tab, open the :guilabel:`Network` tab.

#. Click the :guilabel:`Floating IPs` tab, which shows the floating IP
   addresses allocated to instances.

#. Click :guilabel:`Allocate IP To Project`.

#. Choose the pool from which to pick the IP address.

#. Click :guilabel:`Allocate IP`.

#. In the :guilabel:`Floating IPs` list, click :guilabel:`Associate`.

#. In the :guilabel:`Manage Floating IP Associations` dialog box,
   choose the following options:

   -  The :guilabel:`IP Address` field is filled automatically,
      but you can add a new IP address by clicking the
      :guilabel:`+` button.

   -  In the :guilabel:`Port to be associated` field, select a port
      from the list.

      The list shows all the instances with their fixed IP addresses.

#. Click :guilabel:`Associate`.

.. note::

   To disassociate an IP address from an instance, click the
   :guilabel:`Disassociate` button.

To release the floating IP address back into the floating IP pool, click
the :guilabel:`Release Floating IP` option in the :guilabel:`Actions` column.
