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
    .module('horizon.app.core.keypairs')
    .controller('KeypairController', KeypairController);

  KeypairController.$inject = [
    'horizon.dashboard.project.workflow.launch-instance.basePath',
    'horizon.app.core.openstack-service-api.nova',
    'horizon.framework.widgets.modal-wait-spinner.service',
    '$window',
    '$uibModal'
  ];

  /**
   * @ngdoc controller
   * @name KeypairController
   * @param {string} basePath
   * @param {Object} $uibModal
   * @description
   * Allows creation of key pairs.
   * @returns {undefined} No return value
   */
  function KeypairController(
    basePath,
    nova,
    spinnerService,
    $window,
    $uibModal
  ) {
    var ctrl = this;

    ctrl.createKeyPair = createKeyPair;

    //////////

    function setKeyPairs(config) {
      return function(response) {
        var keyPairs = response.data.items.map(getName);

        $uibModal.open({
          templateUrl: basePath + 'keypair/create-keypair.html',
          controller: 'LaunchInstanceCreateKeyPairController as ctrl',
          windowClass: 'modal-dialog-wizard',
          resolve: {
            existingKeypairs: getKeypairs
          }
        }).result.then(go(config.successUrl));

        function getName(item) {
          return item.keypair.name;
        }

        function getKeypairs() {
          return keyPairs;
        }
      };
    }

    /**
     * @ngdoc function
     * @name createKeyPair
     * @description
     * Launches the modal to create a key pair.
     * @returns {undefined} No return value
     */
    function createKeyPair(config) {
      nova.getKeypairs().then(setKeyPairs(config));
    }

    function go(url) {
      return function changeUrl() {
        spinnerService.showModalSpinner(gettext('Please Wait'));
        $window.location.href = url;
      };
    }

  }

})();
