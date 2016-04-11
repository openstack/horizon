/**
 * (c) Copyright 2015 Hewlett-Packard Development Company, L.P.
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
    .module('horizon.app.core.openstack-service-api')
    .factory('horizon.app.core.openstack-service-api.novaExtensions', novaExtensionsAPI);

  novaExtensionsAPI.$inject = [
    '$cacheFactory',
    'horizon.app.core.openstack-service-api.extensions',
    'horizon.app.core.openstack-service-api.nova'
  ];

  /**
   * @ngdoc service
   * @name novaExtensionsAPI
   * @param {Object} $cacheFactory
   * @param {Object} extensionsAPI
   * @param {Object} novaAPI
   * @description
   * Provides cached access to Nova Extensions with utilities to help
   * with asynchronous data loading. The cache may be reset at any time
   * by accessing the cache and calling removeAll. The next call to any
   * function will retrieve fresh results.
   *
   * The enabled extensions do not change often, so using cached data will
   * speed up results. Even on a local devstack in informal testing,
   * this saved between 30 - 100 ms per request.
   * @returns {Object} The service
   */
  function novaExtensionsAPI($cacheFactory, extensionsAPI, novaAPI) {
    return extensionsAPI({
      cacheFactory: $cacheFactory(
        'horizon.app.core.openstack-service-api.novaExtensions',
        {capacity: 1}
      ),
      serviceAPI: novaAPI
    });
  }
}());
