/*
 * Copyright 2016 IBM Corp.
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
   * @name horizon.framework.util.validators:validateUnique
   * @element ng-model
   * @description
   * The `validateUnique` directive provides validation for form input elements to ensure
   * values are unique.
   *
   * The form input value can be validated against an array of values or a custom validator
   * function can be provided. If an array of values is specified, the validator returns true
   * if the value is not found in the array. If a function is specified, the validator returns
   * the value of the function which should evaluate to true or false.
   *
   * @restrict A
   *
   * @example
   * ```
   * <input type="number" ng-model="value"
   *   validate-unique="[80,443]">
   * ```
   *
   * @example
   * ```
   * <input type="string" ng-model="value"
   *   validate-unique="ctrl.validateUniqueName">
   *
   * ctrl.validateUniqueName = function(value) {
   *   return !existingItems.some(function(item) {
   *     return item.leaf && item.leaf.name === value;
   *   });
   * };
   * ```
   */

  angular
    .module('horizon.framework.util.validators')
    .directive('validateUnique', validateUnique);

  function validateUnique() {
    var directive = {
      require: 'ngModel',
      restrict: 'A',
      link: link
    };

    return directive;

    //////////

    function link(scope, element, attrs, ctrl) {
      ctrl.$parsers.push(validate);
      ctrl.$formatters.push(validate);

      attrs.$observe('validateUnique', function () {
        validate(ctrl.$modelValue);
      });

      function validate(value) {
        var param = scope.$eval(attrs.validateUnique);
        var unique = true;
        if (angular.isArray(param) && param.length > 0) {
          unique = param.indexOf(value) < 0;
        } else if (angular.isFunction(param)) {
          unique = param(value);
        }
        ctrl.$setValidity('unique', unique);
        return value;
      }

    }
  }
})();
