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
(function() {
  'use strict';

  describe('Launch Instance Ports Step', function() {

    beforeEach(module('horizon.framework.widgets'));
    beforeEach(module('horizon.framework.widgets.action-list'));
    beforeEach(module('horizon.dashboard.project.workflow.launch-instance'));

    describe('LaunchInstanceNetworkPortController', function() {
      var ctrl;
      var port = {name: 'test_name', id: 'test_id'};

      beforeEach(inject(function($controller) {
        var model = {
          newInstanceSpec: {
            ports: ['port-a']
          },
          ports: ['port-a', 'port-b']
        };

        ctrl = $controller('LaunchInstanceNetworkPortController',
                          { launchInstanceModel: model });
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

      it('nameOrID returns the name', function() {
        expect(ctrl.nameOrID).toBeDefined();
        expect(ctrl.nameOrID(port)).toBe('test_name');
      });

      it('nameOrID returns the id if the name is missing', function() {
        expect(ctrl.nameOrID).toBeDefined();
        expect(ctrl.nameOrID({'id': 'testid'})).toBe('testid');
      });

      it('getPortsObj returns generated ports object', function() {
        expect(ctrl.getPortsObj).toBeDefined();
        expect(ctrl.isPortsObjGenerated).toBe(false);
        expect(ctrl.getPortsObj([port])).toEqual({'test_id': port});
        expect(ctrl.isPortsObjGenerated).toBe(true);
      });

      it('getPortsObj returns existing ports object', function() {
        ctrl.portsObj = {'test_id': port};
        ctrl.isPortsObjGenerated = true;
        expect(ctrl.getPortsObj).toBeDefined();
        expect(ctrl.getPortsObj([port])).toEqual({'test_id': port});
      });

      it('uses scope to set table data', function() {
        expect(ctrl.tableDataMulti).toBeDefined();
        expect(ctrl.tableDataMulti.available).toEqual(['port-a', 'port-b']);
        expect(ctrl.tableDataMulti.allocated).toEqual(['port-a']);
      });
    });
  });
})();
