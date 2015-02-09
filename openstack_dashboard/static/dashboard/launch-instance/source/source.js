(function () {
  'use strict';

  var module = angular.module('hz.dashboard.launch-instance');

  module.controller('LaunchInstanceSourceCtrl', [
    '$scope',
    LaunchInstanceSourceCtrl
  ]);

  module.controller('LaunchInstanceSourceHelpCtrl', [
    '$scope',
    LaunchInstanceSourceHelpCtrl
  ]);

  function LaunchInstanceSourceCtrl($scope) {
    $scope.title = gettext('Instance Details');
  }

  function LaunchInstanceSourceHelpCtrl($scope) {
    $scope.title = gettext('Instance Details Help');
  }

})();
