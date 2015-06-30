/*
 *    (c) Copyright 2015 Hewlett-Packard Development Company, L.P.
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *    http://www.apache.org/licenses/LICENSE-2.0
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
   * @name LaunchInstanceNetworkController
   * @description
   * Controller for the Launch Instance - Network Step.
   */
  angular
    .module('horizon.dashboard.project.workflow.launch-instance')
    .controller('LaunchInstanceNetworkController', LaunchInstanceNetworkController);

  LaunchInstanceNetworkController.$inject = ['$scope'];

  function LaunchInstanceNetworkController($scope) {
    var ctrl = this;

    ctrl.label = {
      title: gettext('Networks'),
      subtitle: gettext('Networks provide the communication channels for instances in the cloud.'),
      network: gettext('Network'),
      subnet_associated: gettext('Subnets Associated'),
      shared: gettext('Shared'),
      admin_state: gettext('Admin State'),
      status: gettext('Status'),
      profile: gettext('Profile'),
      none_option: gettext('(None)'),
      id: gettext('ID'),
      project_id: gettext('Project'),
      external_network: gettext('External Network'),
      provider_network: gettext('Provider Network'),
      provider_network_type: gettext('Type'),
      provider_segmentation_id: gettext('Segmentation ID'),
      provider_physical_network: gettext('Physical Network')
    };

    ctrl.networkStatuses = {
      'ACTIVE': gettext('Active'),
      'DOWN': gettext('Down')
    };

    ctrl.networkAdminStates = {
      'UP': gettext('Up'),
      'DOWN': gettext('Down')
    };

    ctrl.tableDataMulti = {
      available: $scope.model.networks,
      allocated: $scope.model.newInstanceSpec.networks,
      displayedAvailable: [],
      displayedAllocated: []
    };

    ctrl.tableLimits = {
      maxAllocation: -1
    };

    ctrl.tableHelpText = {
      allocHelpText: gettext('Select networks from those listed below.'),
      availHelpText: gettext('Select at least one network')
    };
  }
})();
