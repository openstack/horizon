/**
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
   * @name check-copy-destination
   * @element
   * @description
   * The `check-copy-destination` directive is used on an angular form
   * element to verify whether a copy destination is valid or not.
   *
   * This directive is called if value of dest_container or dest_name is changed,
   * then check following.
   * - destination container correctly exists or not.
   * - destination object does not exists.(To prevent over writeby mistake)
   */
  angular
    .module('horizon.dashboard.project.containers')
    .directive('checkCopyDestination', CheckCopyDestination);

  CheckCopyDestination.$inject = [
    'horizon.app.core.openstack-service-api.swift',
    'horizon.dashboard.project.containers.containers-model',
    '$q'
  ];

  function CheckCopyDestination(swiftAPI, model, $q) {

    /**
     * functions that is used from inside of directive.
     * These function will return just exist or not as true or false.
     */
    function checkContainer(container) {
      var def = $q.defer();
      swiftAPI
        .getContainer(container, true)
        .then(def.resolve, def.reject);
      return def.promise;
    }

    function checkObject(container, object) {
      var def = $q.defer();
      swiftAPI
        .getObjectDetails(container, object, true)
        .then(def.resolve, def.reject);
      return def.promise;
    }

    return {
      restrict: 'A',
      require: 'ngModel',
      link: function(scope, element, attrs, ngModel) {

        var ctrl = scope.ctrl;

        scope.$watch(function() {
          /**
           * function that returns watching target.
           * In this case, if either dest_container or dest_name is changed,
           * second argument(this is also function) will be called.
           * 3rd argment(true) means watch element of return value from 1st argument.
           * (=not only reference to array)
           */
          var destContainer = (ctrl.model.dest_container === undefined ||
            ctrl.model.dest_container === null) ? "" : ctrl.model.dest_container;
          var destName = (ctrl.model.dest_name === undefined ||
            ctrl.model.dest_name === null) ? "" : ctrl.model.dest_name;
          return [destContainer, destName];

        }, function (value) {
          /**
           * These function set validity according to
           * API execution result.
           *
           *    If exepected value is "exist" like contianer,
           *    error will not be set if object (correctly) exist.
           *
           *    If exepected value is "does not exist" like object,
           *    error will be set if object exist.
           */
          var destContainer = value[0];
          var destName = value[1];

          ngModel.$setValidity('containerNotFound', true);
          ngModel.$setValidity('objectExists', true);

          if (destContainer === "") {
            return value;
          }

          checkContainer(destContainer).then(
            function success() {
              ngModel.$setValidity('containerNotFound', true);
              return value;
            },
            function error() {
              ngModel.$setValidity('containerNotFound', false);
              return;
            }
          );

          if (destName !== "") {
            checkObject(destContainer, destName).then(
              function success() {
                ngModel.$setValidity('objectExists', false);
                return;
              },
              function error () {
                ngModel.$setValidity('objectExists', true);
                return value;
              }
            );
          }

        }, true);
      }
    };
  }
})();
