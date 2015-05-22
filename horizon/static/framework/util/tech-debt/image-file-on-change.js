(function () {
  'use strict';
  angular.module('horizon.framework.util.tech-debt')

  .directive('imageFileOnChange', function () {
    return {
      require: 'ngModel',
      restrict: 'A',
      link: function ($scope, element, attrs, ngModel) {
        element.bind('change', function (event) {
          var files = event.target.files, file = files[0];
          ngModel.$setViewValue(file);
          $scope.$apply();
        });
      }
    };
  });
}());
