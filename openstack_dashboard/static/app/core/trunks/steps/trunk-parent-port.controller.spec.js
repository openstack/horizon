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

  describe('Create Trunks Parent Step', function() {
    beforeEach(module('horizon.framework.widgets'));
    beforeEach(module('horizon.framework.widgets.action-list'));
    beforeEach(module('horizon.app.core.trunks'));

    describe('TrunkParentPortController', function() {
      var scope, ctrl, ttevents;

      beforeEach(inject(function($rootScope, $controller, $injector) {
        scope = $rootScope.$new();
        scope.crossHide = true;
        scope.ports = {
          parentPortCandidates: [{id: 1}, {id: 2}]
        };
        scope.stepModels = {};
        scope.initTrunk = {
          port_id: 1
        };

        ttevents = $injector.get('horizon.framework.widgets.transfer-table.events');

        ctrl = $controller('TrunkParentPortController', {
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

      it('defines a single-allocation table', function() {
        expect(ctrl.tableLimits).toBeDefined();
        expect(ctrl.tableLimits.maxAllocation).toBe(1);
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
        expect(ctrl.parentTables).toBeDefined();
        expect(ctrl.parentTables.available).toEqual(
          [{id: 1}, {id: 2}]);
        expect(ctrl.parentTables.allocated).toEqual([]);
        expect(ctrl.parentTables.displayedAllocated).toEqual([]);
        expect(ctrl.parentTables.displayedAvailable).toEqual([]);
      });

      it('should return with parent port', function() {
        ctrl.parentTables.allocated = [{id: 3}];
        var trunk = scope.stepModels.trunkSlices.getParentPort();
        expect(trunk.port_id).toEqual(3);
      });

      it('should throw exception if more than on port is allocated', function() {
        ctrl.parentTables.allocated = [{id: 3}, {id: 4}];
        expect(scope.stepModels.trunkSlices.getParentPort).toThrow();
      });

      it('should remove port from available list if subportstable changes', function() {
        spyOn(scope, '$broadcast').and.callThrough();

        ctrl.parentTables.available = [{id: 1}, {id: 2}, {id: 3}];
        scope.stepModels.allocated.subports = [{id: 3}];

        scope.$digest();

        expect(scope.$broadcast).toHaveBeenCalledWith(
          ttevents.TABLES_CHANGED,
          {data: {available: [{id: 1}, {id: 2}]}}
        );
        expect(ctrl.parentTables.available).toEqual([{id: 1}, {id: 2}]);
      });

    });

  });
})();
