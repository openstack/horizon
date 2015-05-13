(function() {
  'use strict';

  /**
   * @ngdoc overview
   * @name hz.framework.validators
   * @description
   *
   * # hz.framework.validators
   *
   * The `hz.framework.validators` module provides support for validating
   * forms.
   *
   * | Directives                                                                      |
   * |---------------------------------------------------------------------------------|
   * | {@link hz.framework.validators.directive:validateNumberMax `validateNumberMax`} |
   * | {@link hz.framework.validators.directive:validateNumberMin `validateNumberMin`} |
   *
   */
  angular.module('hz.framework.validators', [])

    /**
     * @ngdoc directive
     * @name hz.framework.validators.directive:validateNumberMax
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
    .directive('validateNumberMax', [ function() {
      return {
        require: 'ngModel',
        restrict: 'A',
        link: function (scope, element, attrs, ctrl) {
          if (!ctrl) {
            return;
          }

          var maxValidator = function(value) {
            var max = scope.$eval(attrs.validateNumberMax);
            if (angular.isDefined(max) && !ctrl.$isEmpty(value) && value > max) {
              ctrl.$setValidity('validateNumberMax', false);
            } else {
              ctrl.$setValidity('validateNumberMax', true);
            }

            // Return the value rather than undefined if invalid
            return value;
          };

          // Re-validate if value is changed through the UI
          // or model (programmatically)
          ctrl.$parsers.push(maxValidator);
          ctrl.$formatters.push(maxValidator);

          attrs.$observe('validateNumberMax', function() {
            maxValidator(ctrl.$modelValue);
          });
        }
      };
    }])

    /**
     * @ngdoc directive
     * @name hz.framework.validators.directive:validateNumberMin
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
    .directive('validateNumberMin', [ function() {
      return {
        require: 'ngModel',
        restrict: 'A',
        link: function (scope, element, attrs, ctrl) {
          if (!ctrl) {
            return;
          }

          var minValidator = function(value) {
            var min = scope.$eval(attrs.validateNumberMin);
            if (angular.isDefined(min) && !ctrl.$isEmpty(value) && value < min) {
              ctrl.$setValidity('validateNumberMin', false);
            } else {
              ctrl.$setValidity('validateNumberMin', true);
            }

            // Return the value rather than undefined if invalid
            return value;
          };

          // Re-validate if value is changed through the UI
          // or model (programmatically)
          ctrl.$parsers.push(minValidator);
          ctrl.$formatters.push(minValidator);

          attrs.$observe('validateNumberMin', function() {
            minValidator(ctrl.$modelValue);
          });
        }
      };
    }]);

}());