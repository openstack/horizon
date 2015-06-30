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

  /**
   * @ngdoc controller
   * @name LaunchInstanceSourceHelpController
   * @description
   * The `LaunchInstanceSourceHelpController` controller provides functions for
   * configuring the help text used within the source step of the
   * Launch Instance Wizard.
   */
  angular
    .module('horizon.dashboard.project.workflow.launch-instance')
    .controller('LaunchInstanceSourceHelpController', LaunchInstanceSourceHelpController);

  function LaunchInstanceSourceHelpController() {
    var ctrl = this;

    ctrl.title = gettext('Select Source Help');

    ctrl.instanceDetailsTitle = gettext('Instance Details');
    ctrl.instanceDetailsParagraphs = [
      /*eslint-disable max-len */
      gettext('An instance name is required and used to help you uniquely identify your instance in the dashboard.'),
      gettext('If you select an availability zone and plan to use the boot from volume option, make sure that the availability zone you select for the instance is the same availability zone where your bootable volume resides.')
      /*eslint-enable max-len */
    ];

    ctrl.instanceSourceTitle = gettext('Instance Source');
    ctrl.instanceSourceParagraphs = [
      /*eslint-disable max-len */
      gettext('If you want to create an instance that uses ephemeral storage, meaning the instance data is lost when the instance is deleted, then choose one of the following boot sources:'),
      gettext('<li><b>Image</b>: This option uses an image to boot the instance.</li>'),
      gettext('<li><b>Instance Snapshot</b>: This option uses an instance snapshot to boot the instance.</li>'),
      gettext('If you want to create an instance that uses persistent storage, meaning the instance data is saved when the instance is deleted, then select one of the following boot options:'),
      gettext('<li><b>Image (with Create New Volume checked)</b>: This options uses an image to boot the instance, and creates a new volume to persist instance data. You can specify volume size and whether to delete the volume on termination of the instance.</li>'),
      gettext('<li><b>Volume</b>: This option uses a volume that already exists. It does not create a new volume. You can choose to delete the volume on termination of the instance. <em>Note: when selecting Volume, you can only launch one instance.</em></li>'),
      gettext('<li><b>Volume Snapshot</b>: This option uses a volume snapshot to boot the instance, and creates a new volume to persist instance data. You can choose to delete the volume on termination of the instance.</li>')
      /*eslint-enable max-len */
    ];
  }
})();
