===================
System Requirements
===================

The Queens release of horizon has the following dependencies.

* Python 2.7
* Django 1.11

  * Django 1.8 to 1.10 are also supported.
    Their support will be dropped in the Rocky release.

* An accessible `keystone <https://docs.openstack.org/keystone/queens/>`_ endpoint

* All other services are optional.
  Horizon supports the following services as of the Queens release.
  If the keystone endpoint for a service is configured,
  horizon detects it and enables its support automatically.

  * `cinder <https://docs.openstack.org/cinder/queens/>`_: Block Storage
  * `glance <https://docs.openstack.org/glance/queens/>`_: Image Management
  * `neutron <https://docs.openstack.org/neutron/queens/>`_: Networking
  * `nova <https://docs.openstack.org/nova/queens/>`_: Compute
  * `swift <https://docs.openstack.org/swift/queens/>`_: Object Storage
  * Horizon also supports many other OpenStack services via plugins. For more
    information, see the :ref:`install-plugin-registry`.
