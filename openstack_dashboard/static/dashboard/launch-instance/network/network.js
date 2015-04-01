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
    LaunchInstanceNetworkHelpCtrl
  ]);

  function LaunchInstanceNetworkCtrl($scope) {

    $scope.label = {
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

  function LaunchInstanceNetworkHelpCtrl() {
    var ctrl = this;

    ctrl.title = gettext('Network Help');

    ctrl.paragraphs = [
      gettext('Provider networks are created by administrators. These networks map to an existing physical network in the data center.'),
      gettext('Project networks are created by users. These networks are fully isolated and are project-specific.'),
      gettext('An <b>External</b> network is set up by an administrator. If you want an instance to communicate outside of the data center, then attach a router between your <b>Project</b> network and the <b>External</b> network. You can use the <b>Network Topology</b> view to connect the router to the two networks.'),
      gettext('A floating IP allows instances to be addressable from an external network. Floating IPs are not allocated to instances at creation time and may be assigned after the instance is created. To attach a floating IP, go to the <b>Instances</b> view and click the <b>Actions</b> menu to the right of an instance. Then, select the <b>Associate Floating IP</b> option and enter the necessary details.'),
      gettext('Administrators set up the pool of floating IPs that are available to attach to instances.')
    ];

    ctrl.networkCharTitle = gettext('Network characteristics');
    ctrl.networkCharParagraphs = [
      gettext('The subnet identifies a sub-section of a network. A subnet is specified in CIDR format. A typical CIDR format looks like <samp>192.xxx.x.x/24</samp>.'),
      gettext('If a network is shared, then all users in the project can access the network.'),
      gettext('When the <b>Admin State</b> for a network is set to <b>Up</b>, then the network is available for use. You can set the <b>Admin State</b> to <b>Down</b> if you are not ready for other users to access the network.'),
      gettext('The status indicates whether the network has an active connection.')
    ];
  }

})();
