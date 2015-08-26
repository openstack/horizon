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
    '$modalInstance',
    'horizon.framework.widgets.metadata.tree.service',
    'horizon.app.core.metadata.service',
    // Dependencies injected with resolve by $modal.open
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
    $modalInstance, metadataTreeService, metadataService,
    available, existing, params
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
      angular.forEach(updated, function(value, key) {
        delete removed[key];
      });

      metadataService
        .editMetadata(params.resource, params.id, updated, Object.keys(removed))
        .then(onEditSuccess, onEditFailure);
    }

    function cancel() {
      $modalInstance.dismiss('cancel');
    }

    function onEditSuccess() {
      $modalInstance.close();
    }

    function onEditFailure() {
      ctrl.saving = false;
    }
  }
})();
