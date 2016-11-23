/*
 * Copyright 2015, Intel Corp.
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
    .module('horizon.app.core.metadata.modal')
    .controller('MetadataModalController', MetadataModalController);

  MetadataModalController.$inject = [
    '$uibModalInstance',
    'horizon.app.core.metadata.service',
    'horizon.framework.widgets.metadata.tree.service',
    'horizon.framework.widgets.toast.service',
    // Dependencies injected with resolve by $uibModal.open
    'available',
    'existing',
    'params'
  ];

  /**
   * @ngdoc controller
   * @name MetadataModalController
   * @description
   * Controller used by `ModalService`
   */
  function MetadataModalController(
    $uibModalInstance, metadataService, metadataTreeService,
    toastService, available, existing, params
  ) {
    var ctrl = this;

    ctrl.cancel = cancel;
    ctrl.resourceType = params.resource;
    ctrl.save = save;
    ctrl.saving = false;
    ctrl.tree = new metadataTreeService.Tree(available.data.items, existing.data);

    function save() {
      ctrl.saving = true;
      var updated = ctrl.tree.getExisting();
      var removed = angular.copy(existing.data);

      // Glance v1 changes metadata property casing in the get request
      // but to remove you still need to send back in using the proper original case.
      // See https://bugs.launchpad.net/horizon/+bug/1606988
      angular.forEach(removed, function bug1606988(value, removedKey) {
        angular.forEach(ctrl.tree.flatTree, function compareToDefinitions(item) {
          if (item.leaf && removedKey.toLocaleLowerCase() === item.leaf.name.toLocaleLowerCase()) {
            delete removed[removedKey];
            removed[item.leaf.name] = value;
          }
        });
      });

      angular.forEach(updated, function(value, key) {
        delete removed[key];
      });

      metadataService
        .editMetadata(params.resource, params.id, updated, Object.keys(removed))
        .then(onEditSuccess, onEditFailure);
    }

    function cancel() {
      $uibModalInstance.dismiss('cancel');
    }

    function onEditSuccess() {
      toastService.add('success', gettext('Metadata was successfully updated.'));
      $uibModalInstance.close();
    }

    function onEditFailure() {
      toastService.add('error', gettext('Unable to update metadata.'));
      ctrl.saving = false;
    }
  }
})();
