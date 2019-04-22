/*
 * Copyright 2016 Symantec Corp.
 *
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
    .controller('LaunchInstanceServerGroupsController', LaunchInstanceServerGroupsController);

  LaunchInstanceServerGroupsController.$inject = [
    'launchInstanceModel'
  ];

  /**
   * @ngdoc controller
   * @name LaunchInstanceServerGroupsController
   * @param {Object} launchInstanceModel
   * @description
   * Allows selection of server groups.
   * @returns {undefined} No return value
   */
  function LaunchInstanceServerGroupsController(launchInstanceModel) {
    var ctrl = this;
    ctrl.policies = {
      'affinity': gettext('Affinity'),
      'anti-affinity': gettext('Anti Affinity'),
      'soft-anti-affinity': gettext('Soft Anti Affinity'),
      'soft-affinity': gettext('Soft Affinity')
    };

    ctrl.tableData = {
      available: launchInstanceModel.serverGroups,
      allocated: launchInstanceModel.newInstanceSpec.server_groups,
      displayedAvailable: [],
      displayedAllocated: []
    };

    ctrl.tableHelp = {
      /*eslint-disable max-len */
      noneAllocText: gettext('Select a server group from the available groups below.'),
      /*eslint-enable max-len */
      availHelpText: gettext('Select one')
    };

    ctrl.tableLimits = {
      maxAllocation: 1
    };
  }
})();
