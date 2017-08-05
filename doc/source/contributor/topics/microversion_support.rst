============================
Horizon Microversion Support
============================

Introduction
============

Several services use API microversions, which allows consumers of that API to
specify an exact version when making a request. This can be useful in ensuring
a feature continues to work as expected across many service releases.

Adding a feature that was introduced in a microversion
======================================================

1. Add the feature to the ``MICROVERSION_FEATURES`` dict in
   ``openstack_dashboard/api/microversions.py`` under the appropriate
   service name. The feature should have at least two versions listed; the
   minimum version (i.e. the version that introduced the feature) and
   the current working version. Providing multiple versions reduces project
   maintenance overheads and helps Horizon work with older service
   deployments.

2. Use the ``is_feature_available`` function for your service to show or hide
   the function.::

     from openstack_dashboard.api import service

     ...

     def allowed(self, request):
         return service.is_feature_available('feature')

3. Send the correct microversion with ``get_microversion`` function in the API
   layer.::

     def resource_list(request):
         try:
             microversion = get_microversion(request, 'feature')
             client = serviceclient(request, microversion)
             return client.resource_list()

Microversion references
=======================

:Nova: https://docs.openstack.org/nova/latest/reference/api-microversion-history.html
:Cinder: https://docs.openstack.org/cinder/latest/contributor/api_microversion_history.html
:API-WG: https://specs.openstack.org/openstack/api-wg/guidelines/microversion_specification.html
