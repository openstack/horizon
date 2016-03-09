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
    .factory('horizon.app.core.openstack-service-api.serviceCatalog', serviceCatalog);

  serviceCatalog.$inject = [
    '$cacheFactory',
    '$q',
    'horizon.app.core.openstack-service-api.keystone',
    'horizon.app.core.openstack-service-api.userSession'
  ];

  /**
   * @ngdoc service
   * @name serviceCatalog
   * @param {Object} $cacheFactory
   * @param {Object} $q
   * @param {Object} keystoneAPI
   * @param {Object} userSession
   * @description
   * Provides cached access to the Service Catalog with utilities to help
   * with asynchronous data loading. The cache may be reset at any time
   * by accessing the cache and calling removeAll. The next call to any
   * function will retrieve fresh results.
   *
   * The cache in current horizon (Kilo non-single page app) only has a
   * lifetime of the current page. The cache is reloaded every time you change
   * panels. It also happens when you change the region selector at the top
   * of the page, and when you log back in.
   *
   * So, at least for now, this seems to be a reliable way that will
   * make only a single request to get user information for a
   * particular page or modal. Making this a service allows it to be injected
   * and used transparently where needed without making every single use of it
   * pass it through as an argument.
   * @returns {Object} The service
   */
  function serviceCatalog($cacheFactory, $q, keystoneAPI, userSession) {

    var service = {
      cache: $cacheFactory(
        'horizon.app.core.openstack-service-api.serviceCatalog',
        {capacity: 1}
      ),
      get: get,
      ifTypeEnabled: ifTypeEnabled
    };

    return service;

    ////////////

    /**
     * @name get
     * @description
     *
     * @example
     *
     ```js
     serviceCatalog.get().then(doSomething, doSomethingElse);
     ```
     * @returns {Object} The service catalog. This is cached.
     */
    function get() {
      return keystoneAPI.serviceCatalog({cache: service.cache}).then(onGetCatalog);
    }

    function onGetCatalog(response) {
      return response.data;
    }

    /**
     * @name ifTypeEnabled
     * @description
     * Checks if the desired service is enabled.  If it is enabled, use the
     * promise returned to execute the desired function.  If it is not enabled,
     * The promise will be rejected.
     *
     * @param {string} desiredType The type of service desired.
     *
     * @example
     * Assume if the network service is enabled, you want to get networks,
     * if it isn't, then you will do something else.
     * Assume getNetworks is a function that hits Neutron.
     * Assume doSomethingElse is a function that does something else if
     * the network service is not enabled (optional)
     *
     ```js
     serviceCatalog.ifTypeEnabled('network').then(getNetworks, doSomethingElse);
     ```
     * @returns {promise} A promise that resolves if true, rejects with error
     */
    function ifTypeEnabled(desiredType) {
      var deferred = $q.defer();

      $q.all(
        {
          session: userSession.get(),
          catalog: service.get()
        }
      ).then(
        onDataLoaded,
        onDataFailure
      );

      function onDataLoaded(d) {
        if (typeHasEndpointsInRegion(d.catalog,
                                     desiredType,
                                     d.session.services_region)) {
          deferred.resolve();
        } else {
          deferred.reject(
            interpolate(
              gettext('Service type is not enabled: %(desiredType)s'),
              {desiredType: desiredType},
              true)
          );
        }
      }

      function onDataFailure() {
        deferred.reject(gettext('Cannot get service catalog from keystone.'));
      }

      return deferred.promise;
    }

    function typeHasEndpointsInRegion(catalog, desiredType, desiredRegion) {
      var matchingSvcs = catalog.filter(function filterByType(svc) {
        return svc.type === desiredType;
      });

      // Ignore region for identity. Identity service endpoint
      // should not change for different regions.
      if (desiredType === 'identity' && matchingSvcs.length > 0) {
        return true;
      } else {
        return matchingSvcs.some(function matchService(svc) {
          return svc.endpoints.some(function matchEndpoint(endpoint) {
            return getEndpointRegion(endpoint) === desiredRegion;
          });
        });
      }
    }

    /*
     * In Keystone V3, region has been deprecated in favor of
     * region_id.
     *
     * This method provides a way to get region that works for
     * both Keystone V2 and V3.
     */
    function getEndpointRegion(endpoint) {
      return endpoint.region_id || endpoint.region;
    }
  }

}());
