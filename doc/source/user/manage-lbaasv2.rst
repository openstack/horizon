=================================
View and manage load balancers v2
=================================

Load-Balancer-as-a-Service (LBaaS) enables networking to distribute incoming
requests evenly among designated instances. This distribution ensures that
the workload is shared predictably among instances and enables more effective
use of system resources. Use one of these load-balancing methods to distribute
incoming requests:

* Round robin: Rotates requests evenly between multiple instances.
* Source IP: Requests from a unique source IP address are consistently
  directed to the same instance.
* Least connections: Allocates requests to the instance with the
  least number of active connections.

As an end user, you can create and manage load balancers and related
objects for users in various projects. You can also delete load balancers
and related objects.

LBaaS v2 has several new concepts to understand:

Load balancer
 The load balancer occupies a neutron network port and
 has an IP address assigned from a subnet.

Listener
 Each port that listens for traffic on a particular load balancer is
 configured separately and tied to the load balancer. Multiple listeners can
 be associated with the same load balancer.

Pool
 A pool is a group of hosts that sits behind the load balancer and
 serves traffic through the load balancer.

Member
 Members are the actual IP addresses that receive traffic from
 the load balancer. Members are associated with pools.

Health monitor
 Members may go offline from time to time and health monitors
 diverts traffic away from members that are not responding properly.
 Health monitors are associated with pools.

View existing load balancers
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

#. Log in to the OpenStack dashboard.
#. On the :guilabel:`Project` tab, open the
   :guilabel:`Network` tab, and click the
   :guilabel:`Load Balancers` category.

   This view shows the list of existing load balancers. To view details
   of any of the load balancers, click on the specific load balancer.

Create a load balancer
~~~~~~~~~~~~~~~~~~~~~~

#. Log in to the OpenStack dashboard.
#. On the :guilabel:`Project` tab, open the
   :guilabel:`Network` tab, and click the
   :guilabel:`Load Balancers` category.
#. Click the :guilabel:`Create Load Balancer` button.

   Use the concepts described in the overview section to fill in
   the necessary information about the load balancer you want to create.

   Keep in mind, the health checks routinely run against each instance
   within a target load balancer and the result of the health check is
   used to determine if the instance receives new connections.

.. note::
   A message indicates whether the action succeeded.

Delete a load balancer
~~~~~~~~~~~~~~~~~~~~~~

#. Select the load balancer you want to delete
   and click the :guilabel:`Delete Load Balancer` button.

   To be deleted successfully, a load balancer must not
   have any listeners or pools associated with
   it. The delete action is also available in the
   :guilabel:`Actions` column for the individual load balancers.

