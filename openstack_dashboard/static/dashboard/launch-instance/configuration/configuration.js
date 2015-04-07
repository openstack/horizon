(function () {
  'use strict';

  var MAX_SCRIPT_SIZE = 16 * 1024,
      DEFAULT_CONFIG_DRIVE = false,
      DEFAULT_USER_DATA = '',
      DEFAULT_DISK_CONFIG = 'AUTO';

  /**
   * @ngdoc overview
   * @name hz.dashboard.launch-instance
   * @description
   *
   * # hz.dashboard.launch-instance
   *
   * The `hz.dashboard.launch-instance` module allows a user
   * to launch an instance via the multi-step wizard framework
   *
   */
  var module = angular.module('hz.dashboard.launch-instance');

  /**
   * @ngdoc controller
   * @name LaunchInstanceConfigurationCtrl
   * @description
   * The `LaunchInstanceConfigurationCtrl` controller is responsible for
   * setting the following instance properties:
   *
   * @property {string} user_data, default to empty string.
   *    The maximum size of user_data is 16 * 1024.
   * @property {string} disk_config, default to `AUTO`.
   * @property {boolean} config_drive, default to false.
   */
  module.controller('LaunchInstanceConfigurationCtrl', [
    '$scope',
    LaunchInstanceConfigurationCtrl
  ]);

  function LaunchInstanceConfigurationCtrl($scope) {

    var config = this,
        newInstanceSpec = $scope.model.newInstanceSpec;

    newInstanceSpec.user_data = DEFAULT_USER_DATA;
    newInstanceSpec.disk_config = DEFAULT_DISK_CONFIG;
    newInstanceSpec.config_drive = DEFAULT_CONFIG_DRIVE;

    config.MAX_SCRIPT_SIZE = MAX_SCRIPT_SIZE;

    config.label = {
      title: gettext('Configuration'),
      subtitle: gettext(''),
      customizationScript: gettext('Customization Script'),
      customizationScriptMax: gettext('(Max: 16Kb)'),
      loadScriptFromFile: gettext('Load script from a file'),
      configurationDrive: gettext('Configuration Drive'),
      diskPartition: gettext('Disk Partition'),
      scriptSize: gettext('Script size'),
      scriptModified: gettext('Modified'),
      scriptSizeWarningMsg: gettext('Script size > 16Kb'),
      bytes: gettext('bytes'),
      scriptSizeHoverWarningMsg: gettext('The maximum script size is 16Kb.')
    };

    config.diskConfigOptions = [
      { value: 'AUTO', text: gettext('Automatic') },
      { value: 'MANUAL', text: gettext('Manual') }
    ];
  }

  /**
   * @ngdoc controller
   * @name LaunchInstanceConfigurationHelpCtrl
   * @description
   * The `LaunchInstanceConfigurationHelpCtrl` controller provides functions for
   * configuring the help text used within the configuration step of the
   * Launch Instance Wizard.
   *
   */
  module.controller('LaunchInstanceConfigurationHelpCtrl', [
    LaunchInstanceConfigurationHelpCtrl
  ]);

  function LaunchInstanceConfigurationHelpCtrl() {
    var ctrl = this;

    ctrl.title = gettext('Configuration Help');

    var customScriptMap = { cloutInit: 'cloud-init' };
    var customScriptText = gettext('Custom scripts are attached to instances to perform specific actions when the instance is launched. For example, if you are unable to install <samp>%(cloutInit)s</samp> inside a guest operating system, you can use a custom script to get a public key and add it to the user account.');

    ctrl.paragraphs = [
      interpolate(customScriptText, customScriptMap, true),
      gettext('Type your script directly into the Customization Script field. If your browser supports the HTML5 File API, you may choose to load your script from a file. The size of your script should not exceed 16 Kb.'),
      gettext('An advanced option available when launching an instance is disk partitioning. There are two disk partition options. Selecting <b>Automatic</b> resizes the disk and sets it to a single partition. Selecting <b>Manual</b> allows you to create multiple partitions on the disk.'),
      gettext('Check the <b>Configuration Drive</b> box if you want to write metadata to a special configuration drive. When the instance boots, it attaches to the <b>Configuration Drive</b> and accesses the metadata.')
    ];
  }

})();
