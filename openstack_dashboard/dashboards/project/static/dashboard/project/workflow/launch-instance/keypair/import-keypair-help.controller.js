/*
 *    (c) Copyright 2015 Hewlett-Packard Development Company, L.P.
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *    http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

(function () {
  'use strict';

  angular
    .module('horizon.dashboard.project.workflow.launch-instance')
    .controller('LaunchInstanceImportKeyPairHelpController',
                LaunchInstanceImportKeyPairHelpController);

  /**
   * @ngdoc controller
   * @name LaunchInstanceImportKeyPairHelpController
   * @description
   * The `LaunchInstanceImportKeyPairHelpController` controller provides help text
   * for the import key pair function within the Launch Instance Wizard.
   *
   */
  function LaunchInstanceImportKeyPairHelpController() {
    var ctrl = this;

    ctrl.title = gettext('Import Key Pair Help');

    var genKeyPairsMap = { genKeyPairCmd: 'ssh-keygen' };
    var keyPathsMap = { privateKeyPath: 'cloud.key', publicKeyPath: 'cloud.key.pub' };
    var windowsCmdMap = { authorizeKeysFile: '.ssh/authorized_keys' };

    /*eslint-disable max-len */
    var genKeyPairsText = gettext('There are two ways to generate a key pair. From a Linux system, generate the key pair with the <samp>%(genKeyPairCmd)s</samp> command:');
    var keyPathText = gettext('This command generates a pair of keys: a private key (%(privateKeyPath)s) and a public key (%(publicKeyPath)s).');
    var windowsCmd = gettext('From a Windows system, you can use PuTTYGen to create private/public keys. Use the PuTTY Key Generator to create and save the keys, then copy the public key in the red highlighted box to your <samp>%(authorizeKeysFile)s</samp> file.');
    /*eslint-enable max-len */

    ctrl.paragraphs = [
      interpolate(genKeyPairsText, genKeyPairsMap, true),
      '<samp>ssh-keygen -t rsa -f cloud.key</samp>',
      interpolate(keyPathText, keyPathsMap, true),
      interpolate(windowsCmd, windowsCmdMap, true)
    ];
  }

})();
