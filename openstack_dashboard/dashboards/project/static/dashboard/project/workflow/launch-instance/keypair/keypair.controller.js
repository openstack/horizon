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
    '$uibModal',
    'horizon.framework.widgets.toast.service',
    'horizon.app.core.openstack-service-api.settings'
  ];

  /**
   * @ngdoc controller
   * @name LaunchInstanceKeypairController
   * @param {string} basePath
   * @param {Object} launchInstanceModel
   * @param {Object} $uibModal
   * @param {Object} toastService
   * @param {Object} settingsService
   * @description
   * Allows selection of key pairs.
   * @returns {undefined} No return value
   */
  function LaunchInstanceKeypairController(
    basePath,
    launchInstanceModel,
    $uibModal,
    toastService,
    settingsService
  ) {
    var ctrl = this;

    ctrl.isKeypairCreated = false;
    ctrl.createdKeypair = {
      name: "",
      regenerateUrl: ""
    };

    ctrl.allocateNewKeyPair = allocateNewKeyPair;
    ctrl.createKeyPair = createKeyPair;
    ctrl.importKeyPair = importKeyPair;
    ctrl.setKeypairRequired = setKeypairRequired;

    ctrl.tableData = {
      available: launchInstanceModel.keypairs,
      allocated: launchInstanceModel.newInstanceSpec.key_pair
    };

    ctrl.availableTableConfig = {
      selectAll: false,
      trackId: 'id',
      detailsTemplateUrl: basePath + 'keypair/keypair-details.html',
      columns: [
        {id: 'name', title: gettext('Name'), priority: 1},
        {id: 'type', title: gettext('Type'), priority: 2},
        {id: 'fingerprint', title: gettext('Fingerprint'), priority: 3}
      ]
    };

    ctrl.allocatedTableConfig = angular.copy(ctrl.availableTableConfig);
    ctrl.allocatedTableConfig.noItemsMessage = gettext(
      'Select a key pair from the available key pairs below.');

    ctrl.filterFacets = [{
      label: gettext('Name'),
      name: 'name',
      singleton: true
    }, {
      label: gettext('Fingerprint'),
      name: 'fingerprint',
      singleton: true
    }, {
      label: gettext('Type'),
      name: 'type',
      singleton: true
    }];

    ctrl.tableLimits = {
      maxAllocation: 1
    };

    ctrl.isKeypairRequired = 0;

    settingsService.getSetting(
      'OPENSTACK_HYPERVISOR_FEATURES.requires_keypair'
    ).then(setKeypairRequired);

    //////////

    /**
     * @ngdoc function
     * @name allocateNewKeyPair
     * @description
     * Allocate the new key pair (after import or create) if nothing is
     * already allocated.
     * @param {Object} newKeyPair The new key pair object to add
     * @returns {undefined} No return value
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
     * @returns {undefined} No return value
     */
    function createKeyPair() {
      $uibModal.open({
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
     * @param {Object} newKeypair The new key pair object
     * @returns {undefined} No return value
     */
    function notifyUserAndAssign(newKeypair) {
      toastService.add('success',
                       interpolate(gettext('Created keypair: %s'),
                                   [newKeypair.name]));
      assignKeypair(newKeypair);
      ctrl.createdKeypair = newKeypair;
      ctrl.isKeypairCreated = true;
    }

    /**
     * @ngdoc function
     * @name importKeyPair
     * @description
     * Launches the modal to import a key pair.
     * @returns {undefined} No return value
     */
    function importKeyPair() {
      $uibModal.open({
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

    /**
     * @ngdoc function
     * @name setKeypairRequired
     * @description
     * Set if a KeyPair is required based on the settings
     * @param {Boolean} setting The requires_keypair setting
     */
    function setKeypairRequired(setting) {
      ctrl.isKeypairRequired = setting ? 1 : 0;
    }
  }

})();
