(function () {
  'use strict';

  angular.module('horizon.dashboard-app')
  .controller('ImageFormCtrl', ['$scope', function ($scope) {
    $scope.selectImageFormat = function (path) {
      if (!path) { return; }
      var format = path.substr(path.lastIndexOf(".") + 1)
                     .toLowerCase().replace(/[^a-z0-9]+/gi, "");
      if ($('#id_disk_format').find('[value=' + format + ']').length !== 0) {
        $scope.diskFormat = format;
      } else {
        $scope.diskFormat = "";
      }
    };
  }]);

}());