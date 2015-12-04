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

  LaunchInstanceNetworkController.$inject = [
    '$scope',
    'horizon.framework.widgets.action-list.button-tooltip.row-warning.service',
    'launchInstanceModel'
  ];

  function LaunchInstanceNetworkController($scope, tooltipService, launchInstanceModel) {
    var ctrl = this;

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
      displayedAllocated: [],
      minItems: 1
    };

    ctrl.tableLimits = {
      maxAllocation: -1
    };

    ctrl.tableHelpText = {
      allocHelpText: gettext('Select networks from those listed below.'),
      availHelpText: gettext('Select at least one network')
    };

    ctrl.tooltipModel = tooltipService;

    /**
     * Filtering - client-side MagicSearch
     */

    // All facets for network step
    ctrl.networkFacets = [
      {
        label: gettext('Name'),
        name: 'name',
        singleton: true
      },
      {
        label: gettext('Shared'),
        name: 'shared',
        singleton: true,
        options: [
          { label: gettext('No'), key: false },
          { label: gettext('Yes'), key: true }
        ]
      },
      {
        label: gettext('Admin State'),
        name: 'admin_state',
        singleton: true,
        options: [
          { label: gettext('Up'), key: "UP" },
          { label: gettext('Down'), key: "DOWN" }
        ]
      },
      {
        label: gettext('Status'),
        name: 'status',
        singleton: true,
        options: [
          { label: gettext('Active'), key: "ACTIVE"},
          { label: gettext('Down'), key: "DOWN" }
        ]
      }
    ];

    function getPorts() {
      return launchInstanceModel.newInstanceSpec.ports;
    }

    function toggleNetworksRequirement(newValue) {
      // if there is a port selected, remove the validate-number-min
      // for networks table
      if (newValue.length > 0) {
        ctrl.tableDataMulti.minItems = 0;
      }
      // if no port is selected restore the validate-number-min value
      if (newValue.length === 0) {
        ctrl.tableDataMulti.minItems = 1;
      }
    }
    // If a port is selected, then networks are not required
    var portWatcher = $scope.$watch(getPorts, toggleNetworksRequirement, true);

    $scope.$on('$destroy', function() {
      portWatcher();
    });
  }

})();
