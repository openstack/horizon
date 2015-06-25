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
   * @name horizon.framework.util.validators.directive:validateNumberMax
   * @element ng-model
   * @description
   * The `validateNumberMax` directive provides max validation
   * for the form input elements. This is an alternative to
   * `max` which doesn't re-evaluate expression passed in on
   * change. This allows the max value to be dynamically
   * specified.
   *
   * The model and view value is not set to undefined if
   * input does not pass validation. This is so that
   * components that are watching this value can determine
   * what to do with it. For example, quota charts can
   * still render and display over-utilized slices in red.
   *
   * Validator returns true if model/view value <= max value.
   *
   * @restrict A
   *
   * @example
   * ```
   * <input type="text" ng-model="value"
   *   validate-number-max="{$ maxNumber $}">
   * ```
   */
  angular
    .module('horizon.framework.util.validators')
    .directive('validateNumberMax', validateNumberMax);

  function validateNumberMax() {
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
      ctrl.$parsers.push(maxValidator);
      ctrl.$formatters.push(maxValidator);

      attrs.$observe('validateNumberMax', function () {
        maxValidator(ctrl.$modelValue);
      });

      function maxValidator(value) {
        var max = scope.$eval(attrs.validateNumberMax);
        if (angular.isDefined(max) && !ctrl.$isEmpty(value) && value > max) {
          ctrl.$setValidity('validateNumberMax', false);
        } else {
          ctrl.$setValidity('validateNumberMax', true);
        }

        // Return the value rather than undefined if invalid
        return value;
      }
    } // end of link
  } // end of validateNumberMax
})();
