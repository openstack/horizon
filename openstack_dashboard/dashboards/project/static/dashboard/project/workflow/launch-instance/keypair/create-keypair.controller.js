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
    .controller('LaunchInstanceCreateKeyPairController', LaunchInstanceCreateKeyPairController);

  LaunchInstanceCreateKeyPairController.$inject = [
    '$uibModalInstance',
    'existingKeypairs',
    'horizon.app.core.openstack-service-api.nova'
  ];

  /**
   * @ngdoc controller
   * @name LaunchInstanceCreateKeyPairController
   * @param {Object} $uibModalInstance
   * @param {Object} existingKeypairs
   * @param {Object} nova
   * @description
   * Provide a dialog for creation of a new key pair.
   * @returns {undefined} Returns nothing
   */
  function LaunchInstanceCreateKeyPairController($uibModalInstance, existingKeypairs, nova) {
    var ctrl = this;

    ctrl.submit = submit;
    ctrl.cancel = cancel;
    ctrl.doesKeypairExist = doesKeypairExist;
    ctrl.generate = generate;

    ctrl.keypair = '';
    ctrl.key_types = {
      'ssh': gettext("SSH Key"),
      'x509': gettext("X509 Certificate")
    };
    ctrl.key_type = 'ssh';
    ctrl.keypairExistsError = gettext('Keypair already exists or name contains bad characters.');
    ctrl.copyPrivateKey = copyPrivateKey;

    ctrl.onKeyTypeChange = function (keyType) {
      ctrl.key_type = keyType;
    };

    /*
     * @ngdoc function
     * @name doesKeypairExist
     * @description
     * Returns true if the key controller's key pair exists.
     */
    function doesKeypairExist() {
      return exists(ctrl.keypair);
    }

    function generate() {
      nova.createKeypair({name: ctrl.keypair, key_type: ctrl.key_type}).then(onKeypairCreated);

      function onKeypairCreated(data) {
        ctrl.createdKeypair = data.data;
        ctrl.privateKey = ctrl.createdKeypair.private_key;
        ctrl.publicKey = ctrl.createdKeypair.public_key;
      }
    }

    function copyPrivateKey() {
      angular.element('textarea').select();
      document.execCommand('copy');
    }

    /*
     * @ngdoc function
     * @name exists
     * @description
     * Returns true if the given key pair name exists.
     * @param {string} keypair The key pair name
     */
    function exists(keypair) {
      return existingKeypairs.indexOf(keypair) !== -1;
    }

    /*
     * @ngdoc function
     * @name submit
     * @description
     * Attempts to create and download the key pair based on parameters
     * on the controller (the name).  If successful, then it captures
     * the URL needed to regenerate the key pair (so the user can elect to
     * regenerate it if they want).  If unsuccessful, then the user is
     * notified of the problem and given the opportunity to try again.
     */
    function submit() {
      $uibModalInstance.close(ctrl.createdKeypair);
    }

    /*
     * @ngdoc function
     * @name cancel
     * @description
     * Dismisses the modal
     */
    function cancel() {
      $uibModalInstance.dismiss();
    }

  }

})();
