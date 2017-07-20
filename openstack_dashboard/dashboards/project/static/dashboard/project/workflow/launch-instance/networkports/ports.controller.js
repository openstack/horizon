/*
 *    (c) Copyright 2016 Red Hat, Inc.
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
   * @name LaunchInstanceNetworkPortController
   * @description
   * Controller for the Launch Instance - Network Step.
   */
  angular
    .module('horizon.dashboard.project.workflow.launch-instance')
    .controller('LaunchInstanceNetworkPortController', LaunchInstanceNetworkPortController);

  LaunchInstanceNetworkPortController.$inject = [
    '$scope',
    'horizon.framework.widgets.action-list.button-tooltip.row-warning.service'
  ];

  function LaunchInstanceNetworkPortController($scope, tooltipService) {
    var ctrl = this;

    ctrl.portStatuses = {
      'ACTIVE': gettext('Active'),
      'DOWN': gettext('Down')
    };

    ctrl.portAdminStates = {
      'UP': gettext('Up'),
      'DOWN': gettext('Down')
    };

    ctrl.vnicTypes = {
      'normal': gettext('Normal'),
      'direct': gettext('Direct'),
      'direct-physical': gettext('Direct Physical'),
      'macvtap': gettext('MacVTap'),
      'baremetal': gettext('Bare Metal'),
      'virtio-forwarder': gettext('Virtio Forwarder')
    };

    ctrl.tableDataMulti = {
      available: $scope.model.ports,
      allocated: $scope.model.newInstanceSpec.ports,
      displayedAvailable: [],
      displayedAllocated: []
    };

    ctrl.tableLimits = {
      maxAllocation: -1
    };

    ctrl.tableHelpText = {
      allocHelpText: gettext('Select ports from those listed below.')
    };

    ctrl.tooltipModel = tooltipService;

    ctrl.nameOrID = function nameOrId(data) {
      return angular.isDefined(data.name) && data.name !== '' ? data.name : data.id;
    };
  }
})();
