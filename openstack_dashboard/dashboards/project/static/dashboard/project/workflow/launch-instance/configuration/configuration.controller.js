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

  var MAX_SCRIPT_SIZE = 16 * 1024;

  angular
    .module('horizon.dashboard.project.workflow.launch-instance')
    .controller('LaunchInstanceConfigurationController', LaunchInstanceConfigurationController);

  /**
   * @ngdoc controller
   * @name LaunchInstanceConfigurationController
   * @description
   * The `LaunchInstanceConfigurationController` controller is responsible for
   * setting the following instance properties:
   *
   * @property {string} user_data, default to empty string.
   *    The maximum size of user_data is 16 * 1024.
   * @property {string} disk_config, default to `AUTO`.
   * @property {boolean} config_drive, default to false.
   * @returns {undefined} Returns nothing
   */
  function LaunchInstanceConfigurationController() {
    var ctrl = this;

    ctrl.MAX_SCRIPT_SIZE = MAX_SCRIPT_SIZE;

    ctrl.diskConfigOptions = [
      { value: 'AUTO', text: gettext('Automatic') },
      { value: 'MANUAL', text: gettext('Manual') }
    ];
  }
})();
