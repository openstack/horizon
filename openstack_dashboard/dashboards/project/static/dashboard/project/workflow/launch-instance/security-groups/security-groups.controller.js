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
    .module('horizon.dashboard.project.workflow.launch-instance')
    .controller('LaunchInstanceSecurityGroupsController', LaunchInstanceSecurityGroupsController);

  LaunchInstanceSecurityGroupsController.$inject = [
    'launchInstanceModel',
    'horizon.dashboard.project.workflow.launch-instance.basePath'
  ];

  /**
   * @ngdoc controller
   * @name LaunchInstanceSecurityGroupsController
   * @param {Object} launchInstanceModel
   * @param {string} basePath
   * @description
   * Allows selection of security groups.
   * @returns {undefined} No return value
   */
  function LaunchInstanceSecurityGroupsController(launchInstanceModel, basePath) {
    var ctrl = this;

    ctrl.tableData = {
      available: launchInstanceModel.securityGroups,
      allocated: launchInstanceModel.newInstanceSpec.security_groups,
      displayedAvailable: [],
      displayedAllocated: []
    };

    ctrl.tableDetails = basePath + 'security-groups/security-group-details.html';

    ctrl.tableHelp = {
      /*eslint-disable max-len */
      noneAllocText: gettext('Select one or more security groups from the available groups below.'),
      /*eslint-enable max-len */
      availHelpText: gettext('Select one or more')
    };

    ctrl.tableLimits = {
      maxAllocation: -1
    };
  }
})();
