(function () {
  'use strict';

  var module = angular.module('hz.dashboard.launch-instance');

  module.controller('LaunchInstanceNetworkCtrl', [
    '$scope',
    LaunchInstanceNetworkCtrl
  ]);

  module.controller('LaunchInstanceNetworkHelpCtrl', [
    '$scope',
    LaunchInstanceNetworkHelpCtrl
  ]);

  function LaunchInstanceNetworkCtrl($scope) {
    $scope.title = gettext('Network');
  }

  function LaunchInstanceNetworkHelpCtrl($scope) {
    $scope.title = gettext('Network Help');
  }

})();
