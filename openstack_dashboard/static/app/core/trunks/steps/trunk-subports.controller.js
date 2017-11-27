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
   * @name TrunkSubPortsController
   * @description
   * Controller responsible for trunk attribute(s):
   *   sub_ports
   * This step has to work with both create and edit actions.
   */
  angular
    .module('horizon.app.core.trunks.actions')
    .controller('TrunkSubPortsController', TrunkSubPortsController);

  TrunkSubPortsController.$inject = [
    '$scope',
    'horizon.app.core.trunks.actions.ports-extra.service',
    'horizon.app.core.trunks.portConstants',
    'horizon.framework.widgets.action-list.button-tooltip.row-warning.service',
    'horizon.framework.widgets.transfer-table.events'
  ];

  function TrunkSubPortsController(
    $scope,
    portsExtra,
    portConstants,
    tooltipService,
    ttevents
  ) {
    var ctrl = this;
    var subportCandidates;

    ctrl.portStatuses = portConstants.statuses;
    ctrl.portAdminStates = portConstants.adminStates;
    ctrl.vnicTypes = portConstants.vnicTypes;

    ctrl.tableHelpText = {
      allocHelpText: gettext('Select from the list of available ports below.'),
      availHelpText: gettext('Select many')
    };

    ctrl.tooltipModel = tooltipService;

    ctrl.nameOrID = function nameOrId(data) {
      return angular.isDefined(data.name) && data.name !== '' ? data.name : data.id;
    };

    ctrl.tableLimits = {
      maxAllocation: -1
    };

    ctrl.segmentationTypesDict = {
      // The first item will be the default type.
      'vlan': [1, 4094],
      'inherit': null
    };
    ctrl.segmentationTypes = Object.keys(ctrl.segmentationTypesDict);
    ctrl.subportsDetails = {};

    $scope.getTrunk.then(function(trunk) {
      trunk.sub_ports.forEach(function(subport) {
        ctrl.subportsDetails[subport.port_id] = {
          segmentation_type: subport.segmentation_type,
          segmentation_id: subport.segmentation_id
        };
      });

      ctrl.trunkLoaded = true;
    });

    $scope.getPortsWithNets.then(function(portsWithNets) {
      var subportsOfInitTrunk = portsWithNets.filter(
        portsExtra.isSubportOfTrunk.bind(null, $scope.initTrunk.id));
      subportCandidates = portsWithNets.filter(
        portsExtra.isSubportCandidate);

      ctrl.subportsTables = {
        available: [].concat(subportsOfInitTrunk, subportCandidates),
        allocated: [].concat(subportsOfInitTrunk),
        displayedAvailable: [],
        displayedAllocated: []
      };

      // See also in the details step controller.
      $scope.stepModels.trunkSlices = $scope.stepModels.trunkSlices || {};
      $scope.stepModels.trunkSlices.getSubports = function() {
        var trunk = {sub_ports: []};

        ctrl.subportsTables.allocated.forEach(function(port) {
          // Subport information comes from two sources, one handled by
          // transfertable, the other from outside of transfertable. We
          // may see the two data structures in an inconsistent state. We
          // skip the inconsistent cases by the following condition.
          if (port.id in ctrl.subportsDetails) {
            trunk.sub_ports.push({
              port_id: port.id,
              segmentation_id: ctrl.subportsDetails[port.id].segmentation_id,
              segmentation_type: ctrl.subportsDetails[port.id].segmentation_type
            });
          }
        });

        return trunk;
      };

      // We expose the allocated table directly to the parent port step
      // controller, so it can set watchers on it and react accordingly...
      $scope.stepModels.allocated = $scope.stepModels.allocated || {};
      $scope.stepModels.allocated.subports = ctrl.subportsTables.allocated;

      // ...and vice versa.
      var deregisterAllocatedWatcher = $scope.$watchCollection(
        'stepModels.allocated.parentPort', hideAllocated);

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
        availableList = subportCandidates.filter(
          function(port) {
            return !(port.id in allocatedDict);
          }
        );

        ctrl.subportsTables.available = availableList;
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
