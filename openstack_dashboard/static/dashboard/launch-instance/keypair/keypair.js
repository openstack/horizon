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
    '$modal',
    'dashboardBasePath',
    LaunchInstanceKeypairCtrl
  ]);

  function LaunchInstanceKeypairCtrl(launchInstanceModel,
                                     $modal,
                                     dashboardBasePath) {
    var ctrl = this;

    ctrl.label = {
      title: gettext('Key Pair'),
      subtitle: gettext('A key pair allows you to SSH into your newly created instance. You may select an existing key pair, import a key pair, or generate a new key pair.'),
      name: gettext('Name'),
      description: gettext('Description'),
      createKeyPair: gettext('Create Key Pair'),
      importKeyPair: gettext('Import Key Pair')
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

    ctrl.tableDetails = dashboardBasePath + 'launch-instance/keypair/keypair-details.html';

    ctrl.tableHelp = {
      noneAllocText: gettext('Select a key pair from the available key pairs below.')
    };

    ctrl.tableLimits = {
      maxAllocation: 1
    };

    // Allocate the new key pair (after import or create)
    // if nothing is already allocated
    ctrl.allocateNewKeyPair = function(newKeyPair) {
      if (ctrl.tableData.allocated.length === 0) {
        ctrl.tableData.allocated.push(newKeyPair);
      }
    };

    ctrl.createKeyPair = function () {
      $modal.open({
        templateUrl: dashboardBasePath + 'launch-instance/keypair/create-keypair.html',
        controller: 'LaunchInstanceCreateKeyPairCtrl as ctrl',
        windowClass: 'modal-dialog-wizard',
      }).result.then(
        function (result) {
          // Nova doesn't set the id in the response so we will use
          // the name as the id. Name is the key used in URLs, etc.
          result.id = result.name;

          $modal.open({
            templateUrl: dashboardBasePath + 'launch-instance/keypair/new-keypair.html',
            controller: 'LaunchInstanceNewKeyPairCtrl as ctrl',
            windowClass: 'modal-dialog-wizard',
            resolve: {
              keypair: function () {
                return result;
              }
            }
          });

          launchInstanceModel.keypairs.push(result);
          ctrl.allocateNewKeyPair(result);
        }
      );
    };

    ctrl.importKeyPair = function () {
      $modal.open({
        templateUrl: dashboardBasePath + 'launch-instance/keypair/import-keypair.html',
        controller: 'LaunchInstanceImportKeyPairCtrl as ctrl',
        windowClass: 'modal-dialog-wizard'
      }).result.then(
        function (result) {
          // Nova doesn't set the id in the response so we will use
          // the name as the id. Name is the key used in URLs, etc.
          result.id = result.name;

          launchInstanceModel.keypairs.push(result);
          ctrl.allocateNewKeyPair(result);
        }
      );
    };
  }

  /**
   * @ngdoc controller
   * @name hz.dashboard.launch-instance.LaunchInstanceKeypairHelpCtrl
   * @description
   * Provide help for selection of a key pair.
   */
  module.controller('LaunchInstanceKeypairHelpCtrl', [
    LaunchInstanceKeypairHelpCtrl
  ]);

  function LaunchInstanceKeypairHelpCtrl() {
    var ctrl = this;

    ctrl.title = gettext('Key Pair Help');

    var genKeyPairsMap = {genKeyPairCmd: 'ssh-keygen'};
    var genKeyPairsText = gettext('There are two ways to generate a key pair. From a Linux system, generate the key pair with the <samp>%(genKeyPairCmd)s</samp> command:');

    var keyPathsMap = {
      privateKeyPath: 'cloud.key',
      publicKeyPath: 'cloud.key.pub'
    };
    var keyPathText = gettext('This command generates a pair of keys: a private key (%(privateKeyPath)s) and a public key (%(publicKeyPath)s).');

    var windowsCmdMap = {authorizeKeysFile: '.ssh/authorized_keys'};
    var windowsCmd = gettext('From a Windows system, you can use PuTTYGen to create private/public keys. Use the PuTTY Key Generator to create and save the keys, then copy the public key in the red highlighted box to your <samp>%(authorizeKeysFile)s</samp> file.');

    ctrl.paragraphs = [
      gettext('The key pair allows you to SSH into the instance.'),
      interpolate(genKeyPairsText, genKeyPairsMap, true),
      '<samp>ssh-keygen -t rsa -f cloud.key</samp>',
      interpolate(keyPathText, keyPathsMap, true),
      interpolate(windowsCmd, windowsCmdMap, true)
    ];
  }

  /**
   * @ngdoc controller
   * @name hz.dashboard.launch-instance.LaunchInstanceCreateKeyPairCtrl
   * @description
   * Provide a dialog for creation of a new key pair.
   */
  module.controller('LaunchInstanceCreateKeyPairCtrl', [
    '$modalInstance',
    'novaAPI',
    LaunchInstanceCreateKeyPairCtrl
  ]);

  function LaunchInstanceCreateKeyPairCtrl($modalInstance, novaAPI) {
    var ctrl = this;

    ctrl.labels = {
      wizardTitle: gettext('Launch Instance'),
      title: gettext('Create Key Pair'),
      help: gettext('Key Pairs are how you login to your instance after it is launched. Choose a key pair name you will recognize.'),
      keyPairName: gettext('Key Pair Name'),
      cancel: gettext('Cancel'),
      ok: gettext('Create Key Pair'),
      required: gettext('Required')
    };

    ctrl.model = { name: '' };
    ctrl.submit = function () {
      novaAPI.createKeypair(ctrl.model)
        .success(function (data) {
          $modalInstance.close(data);

          var successMsg = gettext('Successfully created key pair %(name)s');
          horizon.alert('success', interpolate(successMsg, { name: data.name }, true));
        });
    };
    ctrl.cancel = function () {
      $modalInstance.dismiss();
    };
  }

  /**
   * @ngdoc controller
   * @name hz.dashboard.launch-instance.LaunchInstanceNewKeyPairCtrl
   * @description
   * Provide a dialog for display of the information about a new
   * public/private key pair.
   */
  module.controller('LaunchInstanceNewKeyPairCtrl', [
    '$modalInstance',
    'keypair',
    LaunchInstanceNewKeyPairCtrl
  ]);

  function LaunchInstanceNewKeyPairCtrl($modalInstance, keypair) {
    var ctrl = this;

    ctrl.labels = {
      wizardTitle: gettext('Launch Instance'),
      title: gettext('Private Key'),
      help: gettext('This is your new key pair. Copy this information and keep it secure.'),
      keyPairName: gettext('Key Pair Name'),
      fingerprint: gettext('Fingerprint'),
      privateKey: gettext('Private Key'),
      publicKey: gettext('Public Key'),
      ok: gettext('OK')
    };

    ctrl.keypair = keypair;
    ctrl.ok = function () {
      $modalInstance.dismiss();
    };
  }

  /**
   * @ngdoc controller
   * @name hz.dashboard.launch-instance.LaunchInstanceImportKeyPairCtrl
   * @description
   * Provide a dialog for import of an existing ssh public key.
   */
  module.controller('LaunchInstanceImportKeyPairCtrl', [
    '$modalInstance',
    'novaAPI',
    LaunchInstanceImportKeyPairCtrl
  ]);

  function LaunchInstanceImportKeyPairCtrl($modalInstance, novaAPI) {
    var ctrl = this;

    ctrl.labels = {
      wizardTitle: gettext('Launch Instance'),
      title: gettext('Import Key Pair'),
      help: gettext('Key Pairs are how you login to your instance after it is launched. Choose a key pair name you will recognize and paste your SSH public key into the space provided.'),
      keyPairName: gettext('Key Pair Name'),
      publicKey: gettext('Public Key'),
      cancel: gettext('Cancel'),
      ok: gettext('Import Key Pair'),
      required: gettext('Required')
    };

    ctrl.model = { name: '', public_key: '' };
    ctrl.submit = function () {
      novaAPI.createKeypair(ctrl.model)
        .success(function (data) {
          $modalInstance.close(data);

          var successMsg = gettext('Successfully imported key pair %(name)s');
          horizon.alert('success', interpolate(successMsg, { name: data.name }, true));
        });
    };
    ctrl.cancel = function () {
      $modalInstance.dismiss();
    };
  }

  /**
   * @ngdoc controller
   * @name LaunchInstanceImportKeyPairHelpCtrl
   * @description
   * The `LaunchInstanceImportKeyPairHelpCtrl` controller provides help text
   * for the import key pair function within the Launch Instance Wizard.
   *
   */
  module.controller('LaunchInstanceImportKeyPairHelpCtrl', [
    LaunchInstanceImportKeyPairHelpCtrl
  ]);

  function LaunchInstanceImportKeyPairHelpCtrl() {
    var ctrl = this;

    ctrl.title = gettext('Import Key Pair Help');

    var genKeyPairsMap = { genKeyPairCmd: 'ssh-keygen' };
    var genKeyPairsText = gettext('There are two ways to generate a key pair. From a Linux system, generate the key pair with the <samp>%(genKeyPairCmd)s</samp> command:');

    var keyPathsMap = { privateKeyPath: 'cloud.key', publicKeyPath: 'cloud.key.pub' };
    var keyPathText = gettext('This command generates a pair of keys: a private key (%(privateKeyPath)s) and a public key (%(publicKeyPath)s).');

    var windowsCmdMap = { authorizeKeysFile: '.ssh/authorized_keys' };
    var windowsCmd = gettext('From a Windows system, you can use PuTTYGen to create private/public keys. Use the PuTTY Key Generator to create and save the keys, then copy the public key in the red highlighted box to your <samp>%(authorizeKeysFile)s</samp> file.');

    ctrl.paragraphs = [
      interpolate(genKeyPairsText, genKeyPairsMap, true),
      '<samp>ssh-keygen -t rsa -f cloud.key</samp>',
      interpolate(keyPathText, keyPathsMap, true),
      interpolate(windowsCmd, windowsCmdMap, true)
    ];
  }

})();
