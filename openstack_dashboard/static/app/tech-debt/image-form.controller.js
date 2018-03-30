/*
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 * http://www.apache.org/licenses/LICENSE-2.0
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
    .module('horizon.app.tech-debt')
    .controller('ImageFormController', ImageFormController);

  function ImageFormController() {
    var ctrl = this;

    ctrl.copyFrom = angular.element('#id_image_url').val();
    ctrl.diskFormat = angular.element('#id_disk_format option:selected').val();
    ctrl.selectTitle = $('#id_disk_format').parents('.themable-select').find('.dropdown-title');
    ctrl.selectImageFormat = function (path) {
      if (!path) {
        return;
      }
      var format = path.substr(path.lastIndexOf(".") + 1).toLowerCase().replace(/[^a-z0-9]+/gi, "");

      /* eslint-disable angular/ng_angularelement */
      if ($('#id_disk_format').find('[value=' + format + ']').length !== 0) {
      /* eslint-enable angular/ng_angularelement */
        ctrl.diskFormat = format;
        ctrl.selectTitle.text($('#id_disk_format').find('[value=' + format + ']').text());
      } else {
        ctrl.diskFormat = "";
        ctrl.selectTitle.text($('#id_disk_format').find('option').first().text());
      }
    };
  }

})();
