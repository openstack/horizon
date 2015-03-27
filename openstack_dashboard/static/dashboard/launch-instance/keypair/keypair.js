(function () {
  'use strict';

  var module = angular.module('hz.dashboard.launch-instance');

    /**
   * @ngdoc controller
   * @name hz.dashboard.launch-instance.LaunchInstanceKeypairCtrl
   * @description
   * Allows selection of  key pairs.
   */
  module.controller('LaunchInstanceKeypairCtrl', [
    'launchInstanceModel',
    function (launchInstanceModel) {
      var ctrl = this;

      ctrl.label = {
        title: gettext('Key Pair'),
        subtitle: gettext('Select a key pair.'),
        name: gettext('Name'),
        description: gettext('Description')
      };

      ctrl.tableLabels = {
        fingerprint: gettext('Fingerprint'),
        public_key: gettext('Public Key')
      };

      ctrl.tableData = {
        available: launchInstanceModel.keypairs,
        allocated: launchInstanceModel.newInstanceSpec.key_pair,
        displayedAvailable: [],
        displayedAllocated: []
      };

      ctrl.tableDetails =
        '/static/dashboard/launch-instance/keypair/keypair-details.html';

      ctrl.tableHelp = {
        noneAllocText: gettext('Select a key pair from the available key pairs below.')
      };

      ctrl.tableLimits = {
        maxAllocation: 1
      };

    }
  ]);


   /**
   * @ngdoc controller
   * @name hz.dashboard.launch-instance.LaunchInstanceKeypairHelpCtrl
   * @description
   * Provide help for selection of security groups and key pairs.
   */
  module.controller('LaunchInstanceKeypairHelpCtrl', [function () {
      var ctrl = this;

      ctrl.title = gettext('Key Pair Help');

      var genKeyPairsMap = { genKeyPairCmd: 'ssh-keygen' };
      var genKeyPairsText = gettext('There are two ways to generate a key pair. From a Linux system, generate the key pair with the <samp>%(genKeyPairCmd)s</samp> command:');

      var keyPathsMap = { privateKeyPath: 'cloud.key', publicKeyPath: 'cloud.key.pub' };
      var keyPathText = gettext('This command generates a pair of keys: a private key (%(privateKeyPath)s) and a public key (%(publicKeyPath)s).');

      var windowsCmdMap = { authorizeKeysFile: '.ssh/authorized_keys' };
      var windowsCmd = gettext('From a Windows system, you can use PuTTYGen to create private/public keys. Use the PuTTY Key Generator to create and save the keys, then copy the public key in the red highlighted box to your <samp>%(authorizeKeysFile)s</samp> file.');

      ctrl.paragraphs = [
        gettext('The key pair allows you to SSH into the instance.'),
        interpolate(genKeyPairsText, genKeyPairsMap, true),
        '<samp>ssh-keygen -t rsa -f cloud.key</samp>',
        interpolate(keyPathText, keyPathsMap, true),
        interpolate(windowsCmd, windowsCmdMap, true)
      ];    }
  ]);
})();
