================
Project policies
================

This page collects basic policies on horizon development.

Back-end service support
------------------------

* ``N`` release of horizon supports ``N`` and ``N-1`` releases of
  back-end OpenStack services (like nova, cinder, neutron and so on).
  This allows operators to upgrade horizon separately from other OpenStack
  services.

* Horizon should check features in back-end services through APIs as much as
  possible by using micro-versioning for nova, cinder and so on and API
  extensions for neutron (and others if any).

* Related to the previous item, features available in ``N-3`` releases
  (which means the recent four releases including the development version)
  are assumed without checking the availability of features
  to simplify the implementation.

* Removals and deprecations of back-end feature supports basically follows
  `the standard deprecation policy
  <https://governance.openstack.org/tc/reference/tags/assert_follows-standard-deprecation.html>`__
  defined by the technical committee, but there are some notes.
  Deprecations in back-end services are applied to corresponding horizon
  features automatically and it is allowed to drop some feature from horizon
  without an explicit deprecation.

Django support
--------------

* Horizon usually syncs with
  `Django's Roadmap <https://www.djangoproject.com/weblog/2015/jun/25/roadmap/>`__
  and supports LTS (long term support) versions of Django
  as of the feature freeze of each OpenStack release.
  Supports for other maintained Django versions are optional
  and best-effort.
