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
    '$modalInstance',
    'existingKeypairs',
    'horizon.app.core.openstack-service-api.nova',
    'horizon.framework.widgets.toast.service',
    'horizon.app.core.openstack-service-api.keypair-download-service'
  ];

  /**
   * @ngdoc controller
   * @name horizon.dashboard.project.workflow.launch-instance.LaunchInstanceCreateKeyPairController
   * @description
   * Provide a dialog for creation of a new key pair.
   */
  function LaunchInstanceCreateKeyPairController($modalInstance, existingKeypairs, nova,
  toastService, keypairDownloadService) {
    var ctrl = this;

    ctrl.submit = submit;
    ctrl.cancel = cancel;
    ctrl.doesKeypairExist = doesKeypairExist;

    ctrl.keypair = '';
    ctrl.keypairExistsError = gettext('Keypair already exists or name contains bad characters.');

    /*
     * @ngdoc function
     * @name doesKeypairExist
     * @description
     * Returns true if the key controller's key pair exists.
     */
    function doesKeypairExist() {
      return exists(ctrl.keypair);
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
      keypairDownloadService.createAndDownloadKeypair(ctrl.keypair).then(
        function success(createdKeypair) {
          createdKeypair.regenerateUrl = nova.getRegenerateKeypairUrl(createdKeypair.name);
          $modalInstance.close(createdKeypair);
        },
        function error() {
          var errorMessage = gettext('Unable to generate') + ' "' + ctrl.keypair + '". ' +
            gettext('Please try again.');
          toastService.add('error', errorMessage);
        }
      );
    }

    /*
     * @ngdoc function
     * @name cancel
     * @description
     * Dismisses the modal
     */
    function cancel() {
      $modalInstance.dismiss();
    }

  }

})();
