/*
 * (c) Copyright 2015 ThoughtWorks Inc.
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
    .directive('hzIfServices', hzIfServices);

  hzIfServices.$inject = [
    'hzPromiseToggleTemplateDirective',
    'horizon.app.core.openstack-service-api.serviceCatalog'
  ];

  /**
   * @ngdoc directive
   * @name horizon.app.core.cloud-services:directive:hzIfServices
   * @module horizon.app.core.cloud-services
   * @description
   *
   * The hz-if-services attribute should be set to the required service
   * type(s) from the service catalog (e.g. network, volume, search, etc)
   * for the currently scoped region. If the cloud service(s) is available
   * for the current region the content will be evaluated. Otherwise,
   * the content will not be compiled.
   *
   * It may by set to a single service type or an array of service types.
   * This may be done inline or may come from an object in scope.
   *
   * All of the following are valid examples:
   *
   * hz-if-services='"network"'
   * hz-if-services='["network"]'
   * hz-if-services='["network", "metering"]'
   *
   * For using a scope object, assume the following is in the controller:
   *
   * ctrl.requiredServices = ["network", "metering"];
   *
   * Then in HTML:
   *
   * hz-if-services='ctrl.requiredServices'
   *
   * This is evaluated once per page load. In current horizon,
   * this means it will get re-evaluated with events like the
   * user opening another panel, changing logins, or changing their region.
   *
   * @example
   *
   * In the following example, if the network service is not enabled
   * in the service catalog, then the div element with hz-if-services
   * and all of the elements inside of it will be removed and never
   * evaluated by the angular compiler.
   *
   ```html
    <div hz-if-services='\"volume\"'>
      <div class="checkbox customization-script-source">
        <label>
          <input type="number"
                 ng-model="ctrl.defaults.gigabytes">
          Gigabytes
        </label>
      </div>
    </div>
   ```
   */
  function hzIfServices(hzPromiseToggleTemplateDirective, serviceCatalog) {
    return angular.extend(
      hzPromiseToggleTemplateDirective[0],
      {
        singlePromiseResolver: serviceCatalog.ifTypeEnabled,
        name: 'hzIfServices'
      }
    );
  }

})();
