/*
 *    (c) Copyright 2015 Rackspace US, Inc
 *
 * Licensed under the Apache License, Version 2.0 (the 'License');
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *    http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an 'AS IS' BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */
(function () {
  'use strict';

  /**
   * @ngdoc directive
   * @name object-name-exists
   * @element
   * @description
   * The `object-name-exists` directive is used on an angular form
   * element to verify whether a Swift object name in the current context
   * already exists or not. The current context (container name and
   * folder) is taken from the container model service.
   *
   * If the name is taken, the ngModel will have $error.exists set
   * (and all the other usual validation properties).
   *
   * Additionally since the check is asynchronous the ngModel
   * will also have $pending.exists set while the lookup is being
   * performed.
   *
   * @example
   * ```
   *  <input type="text" name="name" ng-model="ctrl.name" object-name-exists>
   *  <span ng-show="ctrl.form.name.$pending.exists">Checking if this name is used...</span>
   *  <span ng-show="ctrl.form.name.$error.exists">This name already exists!</span>
   * ```
   */
  angular
    .module('horizon.dashboard.project.containers')
    .directive('objectNameExists', ObjectNameExists);

  ObjectNameExists.$inject = [
    'horizon.app.core.openstack-service-api.swift',
    'horizon.dashboard.project.containers.containers-model',
    '$q'
  ];

  function ObjectNameExists(swiftAPI, model, $q) {
    return {
      restrict: 'A',
      require: 'ngModel',
      link: function(scope, element, attrs, ngModel) {
        ngModel.$asyncValidators.exists = function exists(modelValue) {
          if (ngModel.$isEmpty(modelValue)) {
            // consider empty model valid
            return $q.when();
          }

          var def = $q.defer();
          // reverse the sense here - successful lookup == error
          swiftAPI
            .getObjectDetails(model.container.name, model.fullPath(modelValue), true)
            .then(def.reject, def.resolve);
          return def.promise;
        };
      }
    };
  }
})();
