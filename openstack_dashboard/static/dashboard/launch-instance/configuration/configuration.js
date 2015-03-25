(function () {
  'use strict';

  var module = angular.module('hz.dashboard.launch-instance');

  module.controller('LaunchInstanceConfigurationCtrl', [
    '$scope',
    LaunchInstanceConfigurationCtrl
  ]);

  module.controller('LaunchInstanceConfigurationHelpCtrl', [
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

  function LaunchInstanceConfigurationHelpCtrl() {
    var ctrl = this;

    ctrl.title = gettext('Configuration Help');

    var customScriptMap = { cloutInit: 'cloud-init' };
    var customScriptText = gettext('Custom scripts are attached to instances to perform specific actions when the instance is launched. For example, if you are unable to install <samp>%(cloutInit)s</samp> inside a guest operating system, you can use a custom script to get a public key and add it to the user account.');

    ctrl.paragraphs = [
      interpolate(customScriptText, customScriptMap, true),
      gettext('The <b>Customization Script Source</b> field determines how the script information is delivered. Use <b>Direct Input</b> if you want to type the script directly into the <b>Customization Script</b> field.'),
      gettext('Check the <b>Configuration Drive</b> box if you want to write metadata to a special configuration drive. When the instance boots, it attaches to the <b>Configuration Drive</b> and accesses the metadata.'),
      gettext('An advanced option available when launching an instance is disk partitioning. There are two disk partition options. Selecting <b>Automatic</b> resizes the disk and sets it to a single partition. Selecting <b>Manual</b> allows you to create multiple partitions on the disk.')
    ];
  }

})();
