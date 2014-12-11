(function () {
  'use strict';
  angular.module('hz')
    .directive('notBlank', function () {
      return {
        require: 'ngModel',
        link: function (scope, elm, attrs, ctrl) {
          ctrl.$parsers.unshift(function (viewValue) {
            if (viewValue.length) {
              // it is valid
              ctrl.$setValidity('notBlank', true);
              return viewValue;
            }
            // it is invalid, return undefined (no model update)
            ctrl.$setValidity('notBlank', false);
            return undefined;
          });
        }
      };
    });
}());