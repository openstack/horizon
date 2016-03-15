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
    .controller('UploadObjectModalController', UploadObjectModalController);

  UploadObjectModalController.$inject = [
    'horizon.dashboard.project.containers.containers-model',
    '$scope'
  ];

  function UploadObjectModalController(model, $scope) {
    var ctrl = this;

    ctrl.model = {
      name:'',
      container: model.container,
      folder: model.folder,
      view_file: null,      // file object managed by angular form ngModel
      upload_file: null,    // file object from the DOM element with the actual upload
      DELIMETER: model.DELIMETER
    };
    ctrl.changeFile = changeFile;

    ///////////

    function changeFile(files) {
      if (files.length) {
        // update the upload file & its name
        ctrl.model.upload_file = files[0];
        ctrl.model.name = files[0].name;

        // we're modifying the model value from a DOM event so we need to manually $digest
        $scope.$digest();
      }
    }
  }
})();
