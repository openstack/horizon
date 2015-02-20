(function () {
  'use strict';

  var module = angular.module('hz.dashboard.launch-instance');

  module.controller('LaunchInstanceAccessAndSecurityCtrl', [
    '$scope',
    LaunchInstanceAccessAndSecurityCtrl
  ]);

  module.controller('LaunchInstanceAccessAndSecurityHelpCtrl', [
    '$scope',
    LaunchInstanceAccessAndSecurityHelpCtrl
  ]);

  function LaunchInstanceAccessAndSecurityCtrl($scope) {
    $scope.title = gettext('Access and Security');
  }

  function LaunchInstanceAccessAndSecurityHelpCtrl($scope) {
    $scope.title = gettext('Access and Security Help');
  }

})();
