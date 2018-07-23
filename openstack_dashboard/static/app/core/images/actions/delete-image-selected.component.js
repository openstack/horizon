/**
 * Licensed under the Apache License, Version 2.0 (the "License"); you may
 * not use self file except in compliance with the License. You may obtain
 * a copy of the License at
 *
 *    http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
 * WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
 * License for the specific language governing permissions and limitations
 * under the License.
 */
// The component generally renders the same content as the default batch action
// button with the added complexity of changing the buttons enabled/disabled
// stated based on the 'allowed' state of the passed selected images.
(function() {
  'use strict';

  angular
    .module('horizon.app.core.images.actions')
    .component('deleteImageSelected', {
      controller: controller,
      templateUrl: templateUrl,
      bindings: {
        callback: '=?',
        selected: '<'
      }
    });

  controller.$inject = [
    'horizon.app.core.images.actions.delete-image.service',
    '$q'
  ];

  function controller(deleteImageService, $q) {
    var ctrl = this;

    ctrl.$onInit = function() {
      ctrl.text = gettext('Delete Images');
      ctrl._disable();
    };

    ctrl.$onChanges = function() {
      ctrl._disable();
    };

    ctrl._disable = function() {
      if (ctrl.selected.length === 0) {
        ctrl.disabled = true;
      } else {
        var promises = $.map(ctrl.selected, function(image) {
          return deleteImageService.allowed(image);
        });

        $q.all(promises).then(
          function() {
            ctrl.disabled = false;
          },
          function() {
            ctrl.disabled = true;
          }
        );
      }
    };
  }

  templateUrl.$inject = ['horizon.app.core.images.basePath'];

  function templateUrl(basePath) {
    return basePath + 'actions/delete-image-selected.template.html';
  }

})();
