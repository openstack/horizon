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
   * @ngdoc module
   * @name hz.dashboard.launch-instance
   * @description
   * Module containing functionality for Launch Instance - Network Step.
   */
  var module = angular.module('hz.dashboard.launch-instance');

  /**
   * @ngdoc controller
   * @name LaunchInstanceNetworkCtrl
   * @description
   * Controller for the Launch Instance - Network Step.
   */
  module.controller('LaunchInstanceNetworkCtrl', [
    '$scope',
    LaunchInstanceNetworkCtrl
  ]);

  /**
   * @ngdoc controller
   * @name LaunchInstanceNetworkHelpCtrl
   * @description
   * Controller for the Launch Instance - Network Step Help.
   */
  module.controller('LaunchInstanceNetworkHelpCtrl', [
    '$scope',
    LaunchInstanceNetworkHelpCtrl
  ]);

  function LaunchInstanceNetworkCtrl($scope) {

    $scope.label = {
      title: gettext('Network'),
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

    $scope.networkStatuses = {
      'ACTIVE': gettext('Active'),
      'DOWN': gettext('Down')
    };

    $scope.networkAdminStates = {
      'UP': gettext('Up'),
      'DOWN': gettext('Down')
    };

    $scope.tableDataMulti = {
      available: $scope.model.networks,
      allocated: $scope.model.newInstanceSpec.networks,
      displayedAvailable: [],
      displayedAllocated: []
    };

    $scope.tableLimits = {
      maxAllocation: -1
    };

    $scope.tableHelpText = {
      allocHelpText: gettext('Select networks from those listed below.'),
      availHelpText: gettext('Select at least one network')
    };

  }

  function LaunchInstanceNetworkHelpCtrl($scope) {
    $scope.title = gettext('Network Help');
  }

})();
