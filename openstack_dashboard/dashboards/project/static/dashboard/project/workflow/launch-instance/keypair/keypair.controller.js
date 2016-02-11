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
    .controller('LaunchInstanceKeypairController', LaunchInstanceKeypairController);

  LaunchInstanceKeypairController.$inject = [
    'horizon.dashboard.project.workflow.launch-instance.basePath',
    'launchInstanceModel',
    '$modal',
    'horizon.framework.widgets.toast.service'
  ];

  /**
   * @ngdoc controller
   * @name horizon.dashboard.project.workflow.launch-instance.LaunchInstanceKeypairController
   * @description
   * Allows selection of key pairs.
   */
  function LaunchInstanceKeypairController(basePath, launchInstanceModel, $modal, toastService) {
    var ctrl = this;

    ctrl.isKeypairCreated = false;
    ctrl.createdKeypair = {
      name: "",
      regenerateUrl: ""
    };

    ctrl.allocateNewKeyPair = allocateNewKeyPair;
    ctrl.createKeyPair = createKeyPair;
    ctrl.importKeyPair = importKeyPair;

    ctrl.tableData = {
      available: launchInstanceModel.keypairs,
      allocated: launchInstanceModel.newInstanceSpec.key_pair,
      displayedAvailable: [],
      displayedAllocated: []
    };

    ctrl.tableDetails = basePath + 'keypair/keypair-details.html';

    ctrl.tableLimits = {
      maxAllocation: 1
    };

    //////////

    /**
     * @ngdoc function
     * @name allocateNewKeyPair
     * @description
     * Allocate the new key pair (after import or create) if nothing is
     * already allocated.
     * @param {Object} newKeyPair The new key pair object to add
     */
    function allocateNewKeyPair(newKeyPair) {
      if (ctrl.tableData.allocated.length === 0) {
        ctrl.tableData.allocated.push(newKeyPair);
      }
    }

    /**
     * @ngdoc function
     * @name createKeyPair
     * @description
     * Launches the modal to create a key pair.
     */
    function createKeyPair() {
      $modal.open({
        templateUrl: basePath + 'keypair/create-keypair.html',
        controller: 'LaunchInstanceCreateKeyPairController as ctrl',
        windowClass: 'modal-dialog-wizard',
        resolve: {
          existingKeypairs: getKeypairs
        }
      }).result.then(notifyUserAndAssign);
    }

    /**
     * @ngdoc function
     * @name notifyUserAndAssign
     * @description
     * Informs the user about the created key pair and sets controller
     * values accordingly.
     * @param {Object} newKeyPair The new key pair object
     */
    function notifyUserAndAssign(newKeypair) {
      toastService.add('success', gettext('Created keypair: ' + newKeypair.name));
      assignKeypair(newKeypair);
      ctrl.createdKeypair = newKeypair;
      ctrl.isKeypairCreated = true;
    }

    /**
     * @ngdoc function
     * @name importKeyPair
     * @description
     * Launches the modal to import a key pair.
     */
    function importKeyPair() {
      $modal.open({
        templateUrl: basePath + 'keypair/import-keypair.html',
        controller: 'LaunchInstanceImportKeyPairController as ctrl',
        windowClass: 'modal-dialog-wizard'
      }).result.then(assignKeypair);
    }

    function assignKeypair(keypair) {
      // Nova doesn't set the id in the response so we will use
      // the name as the id. Name is the key used in URLs, etc.
      keypair.id = keypair.name;

      launchInstanceModel.keypairs.push(keypair);
      ctrl.allocateNewKeyPair(keypair);
    }

    function getKeypairs() {
      return launchInstanceModel.keypairs.map(getName);
    }

    function getName(item) {
      return item.name;
    }
  }

})();
