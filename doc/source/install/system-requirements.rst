===================
System Requirements
===================

The Stein release of horizon has the following dependencies.

* Python 2.7 or 3.5
* Django 1.11 or 2.0

  * Django 1.8 to 1.10 are no longer supported since Rocky release.
  * Horizon usually syncs with
    `Django's Roadmap <https://www.djangoproject.com/weblog/2015/jun/25/roadmap/>`__
    and basically supports maintained versions of Django
    as of the feature freeze of each OpenStack release.

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
