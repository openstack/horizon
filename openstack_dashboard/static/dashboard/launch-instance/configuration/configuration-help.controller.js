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
   * @name LaunchInstanceConfigHelpController
   * @description
   * The `LaunchInstanceConfigHelpController` controller provides functions for
   * configuring the help text used within the configuration step of the
   * Launch Instance Wizard.
   *
   */
  angular
    .module('hz.dashboard.launch-instance')
    .controller('LaunchInstanceConfigHelpController', LaunchInstanceConfigHelpController);

  function LaunchInstanceConfigHelpController() {
    var ctrl = this;

    ctrl.title = gettext('Configuration Help');

    // jscs:disable maximumLineLength
    var customScriptMap = { cloutInit: 'cloud-init' };
    var customScriptText = gettext('Custom scripts are attached to instances to perform specific actions when the instance is launched. For example, if you are unable to install <samp>%(cloutInit)s</samp> inside a guest operating system, you can use a custom script to get a public key and add it to the user account.');

    ctrl.paragraphs = [
      interpolate(customScriptText, customScriptMap, true),
      gettext('Type your script directly into the Customization Script field. If your browser supports the HTML5 File API, you may choose to load your script from a file. The size of your script should not exceed 16 Kb.'),
      gettext('An advanced option available when launching an instance is disk partitioning. There are two disk partition options. Selecting <b>Automatic</b> resizes the disk and sets it to a single partition. Selecting <b>Manual</b> allows you to create multiple partitions on the disk.'),
      gettext('Check the <b>Configuration Drive</b> box if you want to write metadata to a special configuration drive. When the instance boots, it attaches to the <b>Configuration Drive</b> and accesses the metadata.')
    ];
    // jscs:enable maximumLineLength
  }
})();
