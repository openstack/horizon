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
      var ctrl = this;

      ctrl.title = gettext('Access and Security Help');

      var genKeyPairsMap = { genKeyPairCmd: 'ssh-keygen' };
      var genKeyPairsText = gettext('There are two ways to generate a key pair. From a Linux system, generate the key pair with the <samp>%(genKeyPairCmd)s</samp> command:');

      var keyPathsMap = { privateKeyPath: 'cloud.key', publicKeyPath: 'cloud.key.pub' };
      var keyPathText = gettext('This command generates a pair of keys: a private key (%(privateKeyPath)s) and a public key (%(publicKeyPath)s).');

      var windowsCmdMap = { authorizeKeysFile: '.ssh/authorized_keys' };
      var windowsCmd = gettext('From a Windows system, you can use PuTTYGen to create private/public keys. Use the PuTTY Key Generator to create and save the keys, then copy the public key in the red highlighted box to your <samp>%(authorizeKeysFile)s</samp> file.');

      ctrl.paragraphs = [
        gettext('Security groups define a set of IP filter rules that determine how network traffic flows to and from an instance. Users can add additional rules to an existing security group to further define the access options for an instance. To create additional rules, go to the <b>Compute | Access & Security</b> view, then find the security group and click <b>Manage Rules</b>.'),
        gettext('Security groups are project-specific and cannot be shared across projects.'),
        gettext('If a security group is not associated with an instance before it is launched, then you will have very limited access to the instance after it is deployed. You will only be able to access the instance from a VNC console.'),
        gettext('The key pair allows you to SSH into the instance.'),
        interpolate(genKeyPairsText, genKeyPairsMap, true),
        '<samp>ssh-keygen -t rsa -f cloud.key</samp>',
        interpolate(keyPathText, keyPathsMap, true),
        interpolate(windowsCmd, windowsCmdMap, true)
      ];
    }
  ]);
})();
