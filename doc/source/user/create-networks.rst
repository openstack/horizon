==========================
Create and manage networks
==========================

The OpenStack Networking service provides a scalable system for managing
the network connectivity within an OpenStack cloud deployment. It can
easily and quickly react to changing network needs (for example,
creating and assigning new IP addresses).

Networking in OpenStack is complex. This section provides the basic
instructions for creating a network and a router. For detailed
information about managing networks, refer to the `OpenStack Networking Guide
<https://docs.openstack.org/neutron/latest/admin/>`__.

Create a network
~~~~~~~~~~~~~~~~

#. Log in to the dashboard.

#. Select the appropriate project from the drop down menu at the top left.

#. On the :guilabel:`Project` tab, open the :guilabel:`Network` tab and
   click :guilabel:`Networks` category.

#. Click :guilabel:`Create Network`.

#. In the :guilabel:`Create Network` dialog box, specify the following values.

   :guilabel:`Network` tab

   :guilabel:`Network Name`: Specify a name to identify the network.

   :guilabel:`Shared`: Share the network with other projects. Non admin users
   are not allowed to set shared option.

   :guilabel:`Admin State`: The state to start the network in.

   :guilabel:`Create Subnet`: Select this check box to create a subnet

   You do not have to specify a subnet when you create a network, but if
   you do not specify a subnet, the network can not be attached to an instance.

   :guilabel:`Subnet` tab

   :guilabel:`Subnet Name`: Specify a name for the subnet.

   :guilabel:`Network Address`: Specify the IP address for the subnet.

   :guilabel:`IP Version`: Select IPv4 or IPv6.

   :guilabel:`Gateway IP`: Specify an IP address for a specific gateway. This
   parameter is optional.

   :guilabel:`Disable Gateway`: Select this check box to disable a gateway IP
   address.

   :guilabel:`Subnet Details` tab

   :guilabel:`Enable DHCP`: Select this check box to enable DHCP.

   :guilabel:`Allocation Pools`: Specify IP address pools.

   :guilabel:`DNS Name Servers`: Specify a name for the DNS server.

   :guilabel:`Host Routes`: Specify the IP address of host routes.

#. Click :guilabel:`Create`.

   The dashboard shows the network on the :guilabel:`Networks` tab.

Create a router
~~~~~~~~~~~~~~~

#. Log in to the dashboard.

#. Select the appropriate project from the drop down menu at the top left.

#. On the :guilabel:`Project` tab, open the :guilabel:`Network` tab and
   click :guilabel:`Routers` category.

#. Click :guilabel:`Create Router`.

#. In the :guilabel:`Create Router` dialog box, specify a name for the router
   and :guilabel:`External Network`, and click :guilabel:`Create Router`.

   The new router is now displayed in the :guilabel:`Routers` tab.

#. To connect a private network to the newly created router, perform the
   following steps:

   A) On the :guilabel:`Routers` tab, click the name of the router.

   B) On the :guilabel:`Router Details` page, click the :guilabel:`Interfaces`
      tab, then click :guilabel:`Add Interface`.

   C) In the :guilabel:`Add Interface` dialog box, select a :guilabel:`Subnet`.

      Optionally, in the :guilabel:`Add Interface` dialog box, set an
      :guilabel:`IP Address` for the router interface for the selected subnet.

      If you choose not to set the :guilabel:`IP Address` value, then by
      default OpenStack Networking uses the first host IP address in the
      subnet.

      The :guilabel:`Router Name` and :guilabel:`Router ID` fields are
      automatically updated.

#. Click :guilabel:`Add Interface`.

You have successfully created the router. You can view the new topology
from the :guilabel:`Network Topology` tab.

Create a port
~~~~~~~~~~~~~

#. Log in to the dashboard.

#. Select the appropriate project from the drop-down menu at the top left.

#. On the :guilabel:`Project` tab, click :guilabel:`Networks` category.

#. Click on the :guilabel:`Network Name` of the network in which the port
   has to be created.

#. Go to the :guilabel:`Ports` tab and click :guilabel:`Create Port`.

#. In the :guilabel:`Create Port` dialog box, specify the following values.

   :guilabel:`Name`: Specify name to identify the port.

   :guilabel:`Device ID`: Device ID attached to the port.

   :guilabel:`Device Owner`: Device owner attached to the port.

   :guilabel:`Binding Host`: The ID of the host where the port is allocated.

   :guilabel:`Binding VNIC Type`: Select the VNIC type that is bound to the
   neutron port.

#. Click :guilabel:`Create Port`.

   The new port is now displayed in the :guilabel:`Ports` list.
