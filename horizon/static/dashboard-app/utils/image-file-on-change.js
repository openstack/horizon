(function () {
  'use strict';
  angular.module('horizon.dashboard-app.utils')

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
