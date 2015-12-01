(function () {
  'use strict';

  var module = angular.module('hz.dashboard.launch-instance');

    /**
   * @ngdoc controller
   * @name hz.dashboard.launch-instance.LaunchInstanceSecurityGroupsCtrl
   * @description
   * Allows selection of security groups.
   */
  module.controller('LaunchInstanceSecurityGroupsCtrl', [
    'launchInstanceModel',
    '$window',
    function (launchInstanceModel, $window) {
      var ctrl = this;

      ctrl.label = {
        title: gettext('Security Groups'),
        subtitle: gettext('Select the security groups.'),
        name: gettext('Name'),
        description: gettext('Description')
      };

      ctrl.tableLabels = {
        direction: gettext('Direction'),
        ethertype: gettext('Ether Type'),
        protocol: gettext('Protocol'),
        port_range_min: gettext('Min Port'),
        port_range_max: gettext('Max Port'),
        remote_ip_prefix: gettext('Remote')
      };

      ctrl.tableData = {
        available: launchInstanceModel.securityGroups,
        allocated: launchInstanceModel.newInstanceSpec.security_groups,
        displayedAvailable: [],
        displayedAllocated: []
      };

      ctrl.tableDetails = $window.STATIC_URL +
        'dashboard/launch-instance/security-groups/security-group-details.html';

      ctrl.tableHelp = {
        noneAllocText: gettext('Select one or more security groups from the available groups below.'),
        availHelpText: gettext('Select one or more')
      };

      ctrl.tableLimits = {
        maxAllocation: -1
      };
    }
  ]);


   /**
   * @ngdoc controller
   * @name hz.dashboard.launch-instance.LaunchInstanceSecurityGroupsHelpCtrl
   * @description
   * Provide help for selection of security groups and key pairs.
   */
  module.controller('LaunchInstanceSecurityGroupsHelpCtrl', [function () {
      var ctrl = this;

      ctrl.title = gettext('Security Groups Help');

      ctrl.paragraphs = [
        gettext('Security groups define a set of IP filter rules that determine how network traffic flows to and from an instance. Users can add additional rules to an existing security group to further define the access options for an instance. To create additional rules, go to the <b>Compute | Access & Security</b> view, then find the security group and click <b>Manage Rules</b>.'),
        gettext('Security groups are project-specific and cannot be shared across projects.'),
        gettext('If a security group is not associated with an instance before it is launched, then you will have very limited access to the instance after it is deployed. You will only be able to access the instance from a VNC console.'),
      ];
    }
  ]);
})();
