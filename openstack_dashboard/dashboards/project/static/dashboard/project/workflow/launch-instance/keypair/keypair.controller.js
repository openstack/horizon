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
    'launchInstanceModel',
    '$modal',
    'horizon.dashboard.project.workflow.launch-instance.basePath'
  ];

  /**
   * @ngdoc controller
   * @name horizon.dashboard.project.workflow.launch-instance.LaunchInstanceKeypairController
   * @description
   * Allows selection of key pairs.
   */
  function LaunchInstanceKeypairController(launchInstanceModel, $modal, basePath) {
    var ctrl = this;

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

    /*
     * Allocate the new key pair (after import or create)
     * if nothing is already allocated
     */
    function allocateNewKeyPair(newKeyPair) {
      if (ctrl.tableData.allocated.length === 0) {
        ctrl.tableData.allocated.push(newKeyPair);
      }
    }

    function createKeyPair() {
      $modal.open({
        templateUrl: basePath + 'keypair/create-keypair.html',
        controller: 'LaunchInstanceCreateKeyPairController as ctrl',
        windowClass: 'modal-dialog-wizard'
      }).result.then(createKeyPairCallback);
    }

    function importKeyPair() {
      $modal.open({
        templateUrl: basePath + 'keypair/import-keypair.html',
        controller: 'LaunchInstanceImportKeyPairController as ctrl',
        windowClass: 'modal-dialog-wizard'
      }).result.then(importKeyPairCallback);
    }

    function createKeyPairCallback(result) {
      // Nova doesn't set the id in the response so we will use
      // the name as the id. Name is the key used in URLs, etc.
      result.id = result.name;

      $modal.open({
        templateUrl: basePath + 'keypair/new-keypair.html',
        controller: 'LaunchInstanceNewKeyPairController as ctrl',
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

    function importKeyPairCallback(result) {
      // Nova doesn't set the id in the response so we will use
      // the name as the id. Name is the key used in URLs, etc.
      result.id = result.name;

      launchInstanceModel.keypairs.push(result);
      ctrl.allocateNewKeyPair(result);
    }
  }

})();
