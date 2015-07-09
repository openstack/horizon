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

  var fromJson = angular.fromJson;
  var isArray = angular.isArray;

  angular.module('horizon.app.core')

  /**
   * @ngdoc factory
   * @name horizon.app.core:factory:cloudServices
   * @module horizon.app.core
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

  .factory('cloudServices', [
    'horizon.openstack-service-api.cinder',
    'horizon.openstack-service-api.glance',
    'horizon.openstack-service-api.keystone',
    'horizon.openstack-service-api.neutron',
    'horizon.openstack-service-api.nova',
    'horizon.openstack-service-api.novaExtensions',
    'horizon.openstack-service-api.security-group',
    'horizon.openstack-service-api.serviceCatalog',
    'horizon.openstack-service-api.settings',

    function (cinderAPI,
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
  ])

  /**
   * @ngdoc factory
   * @name horizon.app.core:factory:ifFeaturesEnabled
   * @module horizon.app.core
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

  .factory('ifFeaturesEnabled', ['$q', 'cloudServices',
    function ($q, cloudServices) {
      return function ifFeaturesEnabled(serviceName, features) {
        // each cloudServices[serviceName].ifEnabled(feature) is an asynchronous
        // operation which returns a promise, thus requiring the use of $q.all
        // to defer.
        return $q.all(
          features.map(function (feature) {
            return cloudServices[serviceName].ifEnabled(feature);
          })
        );//return
      };//return
    }
  ])

  /**
   * @ngdoc factory
   * @name horizon.app.core:factory:createDirectiveSpec
   * @module horizon.app.core
   * @kind function
   * @description
   *
   * A normalized function that can create a directive specification object
   * based on `serviceName`.
   *
   * @param String serviceName The name of the service, e.g. `novaExtensions`.
   * @param String attrName The name of the attribute in the service.
   * @return Object a directive specification object that can be used to
   * create an angular directive.
   */

  .factory('createDirectiveSpec', ['ifFeaturesEnabled',
    function (ifFeaturesEnabled) {
      return function createDirectiveSpec(serviceName, attrName) {

        function link(scope, element, attrs, ctrl, transclude) {
          element.addClass('ng-hide');
          var features = fromJson(attrs[attrName]);
          if (isArray(features)) {
            ifFeaturesEnabled(serviceName, features).then(
              // if the feature is enabled:
              function () {
                element.removeClass('ng-hide');
              },
              // if the feature is not enabled:
              function () {
                element.remove();
              }
            );
          }
          transclude(scope, function (clone) {
            element.append(clone);
          });
        }

        return {
          link: link,
          restrict: 'E',
          transclude: true
        };
      };
    }
  ])

  /**
   * @ngdoc directive
   * @name horizon.app.core:directive:novaExtension
   * @module horizon.app.core
   * @description
   *
   * This is to enable specifying conditional UI in a declarative way.
   * Some UI components should be showing only when some certain extensions
   * are enabled on `novaExtensions` service.
   *
   * @example
   *
   ```html
    <nova-extension required-extensions='["config_drive"]'>
      <div class="checkbox customization-script-source">
        <label>
          <input type="checkbox"
                 ng-model="model.newInstanceSpec.config_drive">
          {$ ::label.configurationDrive $}
        </label>
      </div>
    </nova-extension>

    <nova-extension required-extensions='["disk_config"]'>
      <div class="form-group disk-partition">
        <label for="launch-instance-disk-partition">
          {$ ::label.diskPartition $}
        </label>
        <select class="form-control"
                id="launch-instance-disk-partition"
                ng-model="model.newInstanceSpec.disk_config"
                ng-options="option.value as option.text for option in diskConfigOptions">
        </select>
      </div>
    </nova-extension>
   ```
   */

  .directive('novaExtension', ['createDirectiveSpec',
    function (createDirectiveSpec) {
      return createDirectiveSpec('novaExtensions', 'requiredExtensions');
    }
  ])

  /**
   * @ngdoc directive
   * @name horizon.app.core:directive:settingsService
   * @module horizon.app.core
   * @description
   *
   * This is to enable specifying conditional UI in a declarative way.
   * Some UI components should be showing only when some certain settings
   * are enabled on `settingsService` service.
   *
   * @example
   *
   ```html
    <settings-service required-settings='["something"]'>
      <!-- ui code here -->
    </settings-service>
   ```
   */

  .directive('settingsService', ['createDirectiveSpec',
    function (createDirectiveSpec) {
      return createDirectiveSpec('settingsService', 'requiredSettings');
    }
  ])

;})();
