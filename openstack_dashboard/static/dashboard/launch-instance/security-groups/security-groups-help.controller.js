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
   * @name hz.dashboard.launch-instance.LaunchInstanceSecurityGroupsHelpController
   * @description
   * Provide help for selection of security groups and key pairs.
   */
  angular
    .module('hz.dashboard.launch-instance')
    .controller('LaunchInstanceSecurityGroupsHelpController',
      LaunchInstanceSecurityGroupsHelpController);

  function LaunchInstanceSecurityGroupsHelpController() {
    var vm = this;

    vm.title = gettext('Security Groups Help');

    vm.paragraphs = [
      /*eslint-disable max-len */
      gettext('Security groups define a set of IP filter rules that determine how network traffic flows to and from an instance. Users can add additional rules to an existing security group to further define the access options for an instance. To create additional rules, go to the <b>Compute | Access & Security</b> view, then find the security group and click <b>Manage Rules</b>.'),
      gettext('Security groups are project-specific and cannot be shared across projects.'),
      gettext('If a security group is not associated with an instance before it is launched, then you will have very limited access to the instance after it is deployed. You will only be able to access the instance from a VNC console.')
      /*eslint-enable max-len */
    ];
  }
})();
