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
    .factory('horizon.app.core.cloud-services.ifFeaturesEnabled', ifFeaturesEnabled);

  ifFeaturesEnabled.$inject = ['$q', 'horizon.app.core.cloud-services.cloudServices'];

  /**
   * @ngdoc factory
   * @name horizon.app.core.cloud-services:factory:ifFeaturesEnabled
   * @module horizon.app.core.cloud-services
   * @kind function
   * @description
   *
   * Check to see if all the listed features are enabled on a certain service,
   * which is described by the service name.
   *
   * This is an asynchronous operation.
   *
   * @param String serviceName The name of the service, e.g. `novaExtensions`.
   * @param Array<String> features A list of feature's names.
   * @return Promise the promise of the deferred task that gets resolved
   * when all the sub-tasks are resolved.
   */
  function ifFeaturesEnabled($q, cloudServices) {
    return function ifFeaturesEnabled(serviceName, features) {
      // each cloudServices[serviceName].ifEnabled(feature) is an asynchronous
      // operation which returns a promise, thus requiring the use of $q.all
      // to defer.
      return $q.all(
        features.map(function mapFeatureEnabled(feature) {
          return cloudServices[serviceName].ifEnabled(feature);
        })
      );//return
    };//return
  }

})();
