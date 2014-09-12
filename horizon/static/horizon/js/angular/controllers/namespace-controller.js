(function () {
  'use strict';
  angular.module('hz')
    .controller('hzNamespaceResourceTypeFormController', function($scope, $window) {
      $scope.resource_types = $window.resource_types;

      $scope.saveResourceTypes = function () {
        $scope.resource_types = JSON.stringify($scope.resource_types);
        $scope.namespace = namespace;
      };
    });
}());