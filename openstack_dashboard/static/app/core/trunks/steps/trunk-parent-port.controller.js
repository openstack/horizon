/*
 * Copyright 2017 Ericsson
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

(function() {
  'use strict';

  /**
   * @ngdoc controller
   * @name TrunkParentPortController
   * @description
   * Controller responsible for trunk attribute(s):
   *   port_id (ie. the parent port)
   * This step has to work with edit action only, since a trunk's parent port
   * cannot be updated.
   */
  angular
    .module('horizon.app.core.trunks.actions')
    .controller('TrunkParentPortController', TrunkParentPortController);

  TrunkParentPortController.$inject = [
    '$scope',
    'horizon.app.core.trunks.actions.ports-extra.service',
    'horizon.app.core.trunks.portConstants',
    'horizon.framework.widgets.action-list.button-tooltip.row-warning.service',
    'horizon.framework.widgets.transfer-table.events'
  ];

  function TrunkParentPortController(
    $scope,
    portsExtra,
    portConstants,
    tooltipService,
    ttevents
  ) {
    var ctrl = this;
    var parentPortCandidates;

    ctrl.portStatuses = portConstants.statuses;
    ctrl.portAdminStates = portConstants.adminStates;
    ctrl.vnicTypes = portConstants.vnicTypes;

    ctrl.tableHelpText = {
      allocHelpText: gettext('Select from the list of available ports below.')
    };

    ctrl.tooltipModel = tooltipService;

    ctrl.nameOrID = function nameOrId(data) {
      return angular.isDefined(data.name) && data.name !== '' ? data.name : data.id;
    };

    ctrl.tableLimits = {
      maxAllocation: 1
    };

    $scope.getPortsWithNets.then(function(portsWithNets) {
      parentPortCandidates = portsWithNets.filter(
        portsExtra.isParentPortCandidate);

      ctrl.parentTables = {
        available: parentPortCandidates,
        allocated: [],
        displayedAvailable: [],
        displayedAllocated: []
      };

      // See also in the details step controller.
      $scope.stepModels.trunkSlices = $scope.stepModels.trunkSlices || {};
      $scope.stepModels.trunkSlices.getParentPort = function() {
        var trunk = {port_id: $scope.initTrunk.port_id};

        if (ctrl.parentTables.allocated.length in [0, 1]) {
          trunk.port_id = ctrl.parentTables.allocated[0].id;
        } else {
          // maxAllocation is 1, so this should never happen.
          throw new Error('Allocating multiple parent ports is meaningless.');
        }

        return trunk;
      };

      // We expose the allocated table directly to the subports step
      // controller, so it can set watchers on it and react accordingly...
      $scope.stepModels.allocated = $scope.stepModels.allocated || {};
      $scope.stepModels.allocated.parentPort = ctrl.parentTables.allocated;

      // ...and vice versa.
      var deregisterAllocatedWatcher = $scope.$watchCollection(
        'stepModels.allocated.subports', hideAllocated);

      $scope.$on('$destroy', function() {
        deregisterAllocatedWatcher();
      });

      function hideAllocated(allocatedList) {
        if (!ctrl.portsLoaded || !allocatedList) {
          return;
        }

        var allocatedDict = {};
        var availableList;

        allocatedList.forEach(function(port) {
          allocatedDict[port.id] = true;
        });
        availableList = parentPortCandidates.filter(
          function(port) {
            return !(port.id in allocatedDict);
          }
        );

        ctrl.parentTables.available = availableList;
        // Notify transfertable.
        $scope.$broadcast(
          ttevents.TABLES_CHANGED,
          {data: {available: availableList}}
        );
      }

      ctrl.portsLoaded = true;
    });

  }
})();
