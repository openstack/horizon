/*
 *    (c) Copyright 2015 Rackspace US, Inc
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
    .controller(
      'horizon.dashboard.project.containers.EditObjectModalController',
      EditObjectModalController
    );

  EditObjectModalController.$inject = ['fileDetails'];

  function EditObjectModalController(fileDetails) {
    var ctrl = this;

    ctrl.model = {
      container: fileDetails.container,
      path: fileDetails.path,
      view_file: null,      // file object managed by angular form ngModel
      edit_file: null       // file object from the DOM element with the actual upload
    };
    ctrl.changeFile = changeFile;

    ///////////

    function changeFile(files) {
      if (files.length) {
        // record the file selected for upload for use in the action that invoked this modal
        ctrl.model.edit_file = files[0];
      }
    }
  }
})();
