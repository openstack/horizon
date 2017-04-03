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

  describe('Create Trunks Subports Step', function() {
    beforeEach(module('horizon.framework.widgets'));
    beforeEach(module('horizon.framework.widgets.action-list'));
    beforeEach(module('horizon.app.core.trunks'));

    describe('TrunkSubPortsController', function() {
      var scope, ctrl, ttevents;

      beforeEach(inject(function($rootScope, $controller, $injector) {
        scope = $rootScope.$new();
        scope.crossHide = true;
        scope.ports = {
          subportCandidates: [{id: 1}, {id: 2}],
          subportsOfInitTrunk: []
        };
        scope.stepModels = {};
        scope.initTrunk = {
          sub_ports: []
        };
        ttevents = $injector.get('horizon.framework.widgets.transfer-table.events');

        ctrl = $controller('TrunkSubPortsController', {
          $scope: scope
        });
      }));

      it('has correct ports statuses', function() {
        expect(ctrl.portStatuses).toBeDefined();
        expect(ctrl.portStatuses.ACTIVE).toBeDefined();
        expect(ctrl.portStatuses.DOWN).toBeDefined();
        expect(Object.keys(ctrl.portStatuses).length).toBe(2);
      });

      it('has correct network admin states', function() {
        expect(ctrl.portAdminStates).toBeDefined();
        expect(ctrl.portAdminStates.UP).toBeDefined();
        expect(ctrl.portAdminStates.DOWN).toBeDefined();
        expect(Object.keys(ctrl.portAdminStates).length).toBe(2);
      });

      it('defines a multiple-allocation table', function() {
        expect(ctrl.tableLimits).toBeDefined();
        expect(ctrl.tableLimits.maxAllocation).toBe(-1);
      });

      it('contains help text for the table', function() {
        expect(ctrl.tableHelpText).toBeDefined();
        expect(ctrl.tableHelpText.allocHelpText).toBeDefined();
      });

      it('nameOrId returns the name', function() {
        var obj = {name: 'test_name', id: 'test_id'};
        expect(ctrl.nameOrID).toBeDefined();
        expect(ctrl.nameOrID(obj)).toBe('test_name');
      });

      it('nameOrId returns the id if the name is missing', function() {
        expect(ctrl.nameOrID).toBeDefined();
        expect(ctrl.nameOrID({'id': 'testid'})).toBe('testid');
      });

      it('uses scope to set table data', function() {
        expect(ctrl.subportsTables).toBeDefined();
        expect(ctrl.subportsTables.available).toEqual(
          [{id: 1}, {id: 2}]);
        expect(ctrl.subportsTables.allocated).toEqual([]);
        expect(ctrl.subportsTables.displayedAllocated).toEqual([]);
        expect(ctrl.subportsTables.displayedAvailable).toEqual([]);
      });

      it('has segmentation types dict', function() {
        expect(ctrl.segmentationTypesDict).toBeDefined();
        expect(ctrl.segmentationTypesDict.vlan).toBeDefined();
        expect(ctrl.segmentationTypesDict.vlan.length).toEqual(2);
      });

      it('has subports detail dict', function() {
        expect(ctrl.subportsDetails).toBeDefined();
      });

      it('has segmentation types list', function() {
        expect(ctrl.segmentationTypes).toBeDefined();
      });

      it('should return with subports', function() {
        ctrl.subportsTables.allocated = [{id: 3}, {id: 4}, {id: 5}];
        ctrl.subportsDetails = {
          3: {segmentation_type: 'VLAN', segmentation_id: 100},
          4: {segmentation_type: 'VLAN', segmentation_id: 101}
        };
        var subports = scope.stepModels.trunkSlices.getSubports();
        expect(subports).toEqual({
          sub_ports: [
            {port_id: 3, segmentation_id: 100, segmentation_type: 'VLAN'},
            {port_id: 4, segmentation_id: 101, segmentation_type: 'VLAN'}
          ]
        });
      });

      it('should remove port from available list if parenttable changes', function() {
        spyOn(scope, '$broadcast').and.callThrough();

        ctrl.subportsTables.available = [{id: 1}, {id: 2}, {id: 3}];
        scope.stepModels.allocated.parentPort = [{id: 3}];

        scope.$digest();

        expect(scope.$broadcast).toHaveBeenCalledWith(
          ttevents.TABLES_CHANGED,
          {data: {available: [{id: 1}, {id: 2}]}}
        );
        expect(ctrl.subportsTables.available).toEqual([{id: 1}, {id: 2}]);
      });

    });

  });
})();
