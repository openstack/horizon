/*
 *    (c) Copyright 2016 Rackspace US, Inc
 *
 * Licensed under the Apache License, Version 2.0 (the 'License');
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *    http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an 'AS IS' BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

(function () {
  'use strict';

  angular
    .module('horizon.dashboard.project.containers')
    .controller('DeleteObjectsModalController', DeleteObjectsModalController);

  DeleteObjectsModalController.$inject = [
    'horizon.dashboard.project.containers.containers-model',
    'selected', '$uibModalInstance'
  ];

  function DeleteObjectsModalController(model, selected, $uibModalInstance) {
    var ctrl = this;

    ctrl.model = {
      container: model.container,
      collection: [],                   // results to pass to model.recursiveDelete
      counted: {files: 0, folders: 0},  // number discovered
      deleted: {files: 0, folders: 0, failures: 0},  // number deleted (and failed)
      mode: 'discovery',                // which mode we're in "discovery" or "deletion"
      running: true,                    // whether action is still running
      cancel: false                     // whether discovery should be cancelled
    };

    // collect files/folders
    model.recursiveCollect(ctrl.model, selected, ctrl.model.collection)
      .then(function complete() {
        ctrl.model.running = false;
      });

    ctrl.dismiss = function dismiss() {
      ctrl.model.cancel = true;
      $uibModalInstance.dismiss();
    };

    ctrl.action = function action() {
      if (ctrl.model.mode === 'discovery') {
        ctrl.model.mode = 'deletion';
        ctrl.model.running = true;
        return model.recursiveDelete(ctrl.model, {tree: ctrl.model.collection})
          .then(function done() { ctrl.model.running = false; });
      } else {
        $uibModalInstance.close();
      }
    };
  }
}());
