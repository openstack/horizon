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

  /**
   * @ngdoc directive
   * @name horizon.framework.util.validators.directive:validateNumberMin
   * @element ng-model
   * @description
   * The `validateNumberMin` directive provides min validation
   * for form input elements. This is an alternative to `min`
   * which doesn't re-evaluate the expression passed in on
   * change. This allows the min value to be dynamically
   * specified.
   *
   * The model and view value is not set to undefined if
   * input does not pass validation. This is so that
   * components that are watching this value can determine
   * what to do with it. For example, quota charts can
   * still render and display over-utilized slices in red.
   *
   * Validator returns true is model/view value >= min value.
   *
   * @restrict A
   *
   * @example
   * ```
   * <input type="text" ng-model="value"
   *   validate-number-min="{$ minNumber $}">
   * ```
   */
  angular
    .module('horizon.framework.util.validators')
    .directive('validateNumberMin', validateNumberMin);

  function validateNumberMin() {
    var directive = {
      require: 'ngModel',
      restrict: 'A',
      link: link
    };

    return directive;

    //////////

    function link(scope, element, attrs, ctrl) {
      if (!ctrl) {
        return;
      }

      /**
        * Re-validate if value is changed through the UI
        * or model (programmatically)
        */
      ctrl.$parsers.push(minValidator);
      ctrl.$formatters.push(minValidator);

      attrs.$observe('validateNumberMin', function () {
        minValidator(ctrl.$modelValue);
      });

      function minValidator(value) {
        var min = scope.$eval(attrs.validateNumberMin);
        if (angular.isDefined(min) && !ctrl.$isEmpty(value) && value < min) {
          ctrl.$setValidity('validateNumberMin', false);
        } else {
          ctrl.$setValidity('validateNumberMin', true);
        }
        // Return the value rather than undefined if invalid
        return value;
      }

    } // end of link
  } // end of validateNumberMax
})();
