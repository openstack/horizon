(function () {
  'use strict';

  var module = angular.module('hz.dashboard.launch-instance');

  module.controller('LaunchInstancePostCreationCtrl', [
    '$scope',
    LaunchInstancePostCreationCtrl
  ]);
  module.controller('LaunchInstancePostCreationHelpCtrl', [
    '$scope',
    LaunchInstancePostCreationHelpCtrl
  ]);

  function LaunchInstancePostCreationCtrl($scope) {
    $scope.title = gettext('Post Creation');
  }

  function LaunchInstancePostCreationHelpCtrl($scope) {
    $scope.title = gettext('Post Creation Help');
  }

})();
