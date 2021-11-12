===================
System Requirements
===================

The Ussuri release of horizon has the following dependencies.

* Python 3.6 or 3.7

* Django 3.2

  * Django support policy is documented at :ref:`django_support`.

* An accessible `keystone <https://docs.openstack.org/keystone/latest/>`_ endpoint

* All other services are optional.
  Horizon supports the following services as of the Stein release.
  If the keystone endpoint for a service is configured,
  horizon detects it and enables its support automatically.

  * `cinder <https://docs.openstack.org/cinder/latest/>`_: Block Storage
  * `glance <https://docs.openstack.org/glance/latest/>`_: Image Management
  * `neutron <https://docs.openstack.org/neutron/latest/>`_: Networking
  * `nova <https://docs.openstack.org/nova/latest/>`_: Compute
  * `swift <https://docs.openstack.org/swift/latest/>`_: Object Storage
  * Horizon also supports many other OpenStack services via plugins. For more
    information, see the :ref:`install-plugin-registry`.
