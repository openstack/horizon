(function () {
  'use strict';

  var module = angular.module('hz.dashboard.launch-instance');

  module.controller('LaunchInstanceFlavorCtrl', [
    '$scope',
    LaunchInstanceFlavorCtrl
  ]);

  module.controller('LaunchInstanceFlavorHelpCtrl', [
    '$scope',
    LaunchInstanceFlavorHelpCtrl
  ]);

  function LaunchInstanceFlavorCtrl($scope) {
    $scope.title = gettext('Select a Flavor');
  }

  function LaunchInstanceFlavorHelpCtrl($scope) {
    $scope.title = gettext('Flavor Help');
  }

})();
