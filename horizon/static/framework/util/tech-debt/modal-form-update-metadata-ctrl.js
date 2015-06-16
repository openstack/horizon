(function () {
  'use strict';

  angular
    .module('horizon.framework.util.tech-debt')
    .controller('hzModalFormUpdateMetadataCtrl', [
      '$scope', '$window',
      function ($scope, $window) {
        $scope.tree = null;
        $scope.available = $window.available_metadata.namespaces;
        $scope.existing = $window.existing_metadata;

        $scope.saveMetadata = function () {
          var metadata = [];
          angular.forEach($scope.tree.getExisting(), function (value, key) {
            metadata.push({
              key: key,
              value: value
            });
          });
          $scope.metadata = JSON.stringify(metadata);
        };
      }
    ]);
}());
