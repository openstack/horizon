(function () {
  'use strict';

  var module = angular.module('hz.dashboard.launch-instance');

  module.controller('LaunchInstanceConfigurationCtrl', [
    '$scope',
    LaunchInstanceConfigurationCtrl
  ]);

  module.controller('LaunchInstanceConfigurationHelpCtrl', [
    '$scope',
    LaunchInstanceConfigurationHelpCtrl
  ]);

  function LaunchInstanceConfigurationCtrl($scope) {
    $scope.label = {
      title: gettext('Configuration'),
      subtitle: gettext(''),
      customizationScriptSource: gettext('Customization Script Source'),
      customizationScript: gettext('Customization Script'),
      configurationDrive: gettext('Configuration Drive'),
      diskPartition: gettext('Disk Partition'),
      scriptFile: gettext('Script File')
    };

    $scope.scriptSourceOptions = [
      { value: 'selected', text: gettext('Select Script Source') },
      { value: 'raw', text: gettext('Direct Input') },
      { value: 'file', text: gettext('File') }
    ];

    $scope.model.newInstanceSpec.script_source = $scope.scriptSourceOptions[0].value;

    $scope.diskConfigOptions = [
      { value: 'AUTO', text: gettext('Automatic') },
      { value: 'MANUAL', text: gettext('Manual') }
    ];

    $scope.model.newInstanceSpec.disk_config = $scope.diskConfigOptions[0].value;
  }

  function LaunchInstanceConfigurationHelpCtrl($scope) {
    $scope.title = gettext('Configuration Help');
  }

})();
