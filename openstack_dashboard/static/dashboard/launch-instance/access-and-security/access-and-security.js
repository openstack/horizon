(function () {
  'use strict';

  var module = angular.module('hz.dashboard.launch-instance');

    /**
   * @ngdoc controller
   * @name hz.dashboard.launch-instance.LaunchInstanceAccessAndSecurityCtrl
   * @description
   * Allows selection of security groups and key pairs.
   */
  module.controller('LaunchInstanceAccessAndSecurityCtrl', [
    '$scope',
    function ($scope) {
      $scope.label = {
        title: gettext('Access and Security'),
        subtitle: gettext('Select the security groups and a key pair.'),
        security_groups: gettext('Security Groups'),
        key_pairs: gettext('Key Pairs'),
        name: gettext('Name'),
        description: gettext('Description')
      };

      $scope.secGroupTableLabels = {
        direction: gettext('Direction'),
        ethertype: gettext('Ether Type'),
        protocol: gettext('Protocol'),
        port_range_min: gettext('Min Port'),
        port_range_max: gettext('Max Port'),
        remote_ip_prefix: gettext('Remote')
      };

      $scope.secGroupTableData = {
        available: $scope.model.securityGroups,
        allocated: $scope.model.newInstanceSpec.security_groups,
        displayedAvailable: [],
        displayedAllocated: []
      };

      $scope.secGroupTableDetails =
        '/static/dashboard/launch-instance/access-and-security/security-group-details.html';

      $scope.secGroupTableHelp = {
        noneAllocText: gettext('Select one or more security groups from the available groups below.'),
        availHelpText: gettext('Select one or more')
      };

      $scope.secGroupTableLimits = {
        maxAllocation: -1
      };

      $scope.keyPairTableLabels = {
        fingerprint: gettext('Fingerprint'),
        public_key: gettext('Public Key')
      };

      $scope.keyPairTableData = {
        available: $scope.model.keypairs,
        allocated: $scope.model.newInstanceSpec.key_pair,
        displayedAvailable: [],
        displayedAllocated: []
      };

      $scope.keyPairTableDetails =
        '/static/dashboard/launch-instance/access-and-security/keypair-details.html';

      $scope.keyPairTableHelp = {
        noneAllocText: gettext('Select a key pair from the available key pairs below.')
      };

      $scope.keyPairTableLimits = {
        maxAllocation: 1
      };

    }
  ]);


   /**
   * @ngdoc controller
   * @name hz.dashboard.launch-instance.LaunchInstanceAccessAndSecurityHelpCtrl
   * @description
   * Provide help for selection of security groups and key pairs.
   */
  module.controller('LaunchInstanceAccessAndSecurityHelpCtrl', [
    '$scope',
    function ($scope) {
      $scope.title = gettext('Access and Security Help');
    }
  ]);
})();
