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
      var $q, $timeout, $scope, ctrl;

      beforeEach(inject(function(_$q_, _$timeout_, $rootScope, $controller) {
        $q = _$q_;
        $timeout = _$timeout_;
        $scope = $rootScope.$new();
        $scope.getPortsWithNets = $q.when([
          {id: 1, admin_state_up: true, device_owner: ''},
          {id: 2, admin_state_up: true, device_owner: ''}
        ]);
        $scope.stepModels = {};
        var trunk = {
          sub_ports: []
        };
        $scope.initTrunk = trunk;
        $scope.getTrunk = $q.when(trunk);

        ctrl = $controller('TrunkSubPortsController', {
          $scope: $scope
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
        $scope.getPortsWithNets.then(function() {
          expect(ctrl.subportsTables).toBeDefined();
          expect(ctrl.subportsTables.available).toEqual([
            {id: 1, admin_state_up: true, device_owner: ''},
            {id: 2, admin_state_up: true, device_owner: ''}
          ]);
          expect(ctrl.subportsTables.allocated).toEqual([]);
          expect(ctrl.subportsTables.displayedAllocated).toEqual([]);
          expect(ctrl.subportsTables.displayedAvailable).toEqual([]);
        });
        $timeout.flush();
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
        $scope.getPortsWithNets.then(function() {
          ctrl.subportsTables.allocated = [{id: 3}, {id: 4}, {id: 5}];
          ctrl.subportsDetails = {
            3: {segmentation_type: 'VLAN', segmentation_id: 100},
            4: {segmentation_type: 'VLAN', segmentation_id: 101}
          };
          var subports = $scope.stepModels.trunkSlices.getSubports();
          expect(subports).toEqual({
            sub_ports: [
              {port_id: 3, segmentation_id: 100, segmentation_type: 'VLAN'},
              {port_id: 4, segmentation_id: 101, segmentation_type: 'VLAN'}
            ]
          });
        });
        $timeout.flush();
      });

      it('should remove port from available list if parenttable changes', function() {
        $scope.getPortsWithNets = $q.when([
          {id: 1, admin_state_up: true, device_owner: ''},
          {id: 2, admin_state_up: true, device_owner: ''},
          {id: 3, admin_state_up: true, device_owner: ''}
        ]);
        $scope.stepModels.allocated = {};
        $scope.stepModels.allocated.parentPort = [{id: 3}];

        $scope.getPortsWithNets.then(function() {
          ctrl.portsLoaded = true;

          expect(ctrl.subportsTables.available).toEqual([
            {id: 1, admin_state_up: true, device_owner: ''},
            {id: 2, admin_state_up: true, device_owner: ''}
          ]);
        });
        $scope.$digest();
      });

      it('should add to allocated list the subports of the edited trunk', function() {
        inject(function($rootScope, $controller) {
          $scope = $rootScope.$new();
          $scope.getPortsWithNets = $q.when([
            {id: 1, admin_state_up: true, device_owner: ''},
            {id: 4, admin_state_up: true, device_owner: '', trunk_id: 1}
          ]);
          $scope.stepModels = {};
          var trunk = {
            id: 1,
            sub_ports: [
              {port_id: 4, segmentation_type: 'vlan', segmentation_id: 2}
            ]
          };
          $scope.initTrunk = trunk;
          $scope.getTrunk = $q.when(trunk);
          ctrl = $controller('TrunkSubPortsController', {
            $scope: $scope
          });
        });

        $scope.getTrunk.then(function() {
          expect(ctrl.subportsDetails).toBeDefined();
          expect(ctrl.subportsDetails).toEqual({
            4: {
              segmentation_id: 2,
              segmentation_type: 'vlan'
            }
          });
        });
        $scope.getPortsWithNets.then(function() {
          var subports = $scope.stepModels.trunkSlices.getSubports();
          expect(subports).toEqual({
            sub_ports: [
              {port_id: 4, segmentation_id: 2, segmentation_type: 'vlan'}
            ]
          });
        });
        $timeout.flush();
      });
    });

  });
})();
