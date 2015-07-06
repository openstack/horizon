/*
 *    (c) Copyright 2015 Hewlett-Packard Development Company, L.P.
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *    http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

(function () {
  'use strict';

  angular
    .module('horizon.app.core.cloud-services')
    .factory('horizon.app.core.cloud-services.cloudServices', cloudServices);

  cloudServices.$inject = [
    'horizon.app.core.openstack-service-api.cinder',
    'horizon.app.core.openstack-service-api.glance',
    'horizon.app.core.openstack-service-api.keystone',
    'horizon.app.core.openstack-service-api.neutron',
    'horizon.app.core.openstack-service-api.nova',
    'horizon.app.core.openstack-service-api.novaExtensions',
    'horizon.app.core.openstack-service-api.security-group',
    'horizon.app.core.openstack-service-api.serviceCatalog',
    'horizon.app.core.openstack-service-api.settings'
  ];

  /**
   * @ngdoc factory
   * @name horizon.app.core.cloud-services:factory:cloudServices
   * @module horizon.app.core.cloud-services
   * @kind hash table
   * @description
   *
   * Provides a hash table contains all the cloud services so that:
   *
   * 1) Easy to inject all the services since they are injected with one dependency.
   * 2) Provides a way to look up a service by name programmatically.
   *
   * The use of this is currently limited to existing API services. Use at
   * your own risk for extensibility purposes at this time. The API will
   * be evolving in the coming release and backward compatibility is not
   * guaranteed. This also makes no guarantee that the back-end service
   * is actually enabled.
   */
  function cloudServices(
    cinderAPI,
    glanceAPI,
    keystoneAPI,
    neutronAPI,
    novaAPI,
    novaExtensions,
    securityGroup,
    serviceCatalog,
    settingsService) {

    return {
      cinder:           cinderAPI,
      glance:           glanceAPI,
      keystone:         keystoneAPI,
      neutron:          neutronAPI,
      nova:             novaAPI,
      novaExtensions:   novaExtensions,
      securityGroup:    securityGroup,
      serviceCatalog:   serviceCatalog,
      settingsService:  settingsService
    };
  }

})();
