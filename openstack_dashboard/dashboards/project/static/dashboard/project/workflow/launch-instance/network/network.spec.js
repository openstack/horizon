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
(function() {
  'use strict';

  describe('Launch Instance Network Step', function() {

    beforeEach(module('horizon.framework.widgets'));
    beforeEach(module('horizon.framework.widgets.action-list'));
    beforeEach(module('horizon.dashboard.project.workflow.launch-instance'));

    describe('LaunchInstanceNetworkController', function() {
      var scope, ctrl;

      beforeEach(inject(function($controller) {
        scope = {
          model: {
            newInstanceSpec: {
              networks: ['net-a']
            },
            networks: ['net-a', 'net-b']
          }
        };
        ctrl = $controller('LaunchInstanceNetworkController', {
          $scope: scope
        });
      }));

      it('has correct network statuses', function() {
        expect(ctrl.networkStatuses).toBeDefined();
        expect(ctrl.networkStatuses.ACTIVE).toBeDefined();
        expect(ctrl.networkStatuses.DOWN).toBeDefined();
        expect(Object.keys(ctrl.networkStatuses).length).toBe(2);
      });

      it('has correct network admin states', function() {
        expect(ctrl.networkAdminStates).toBeDefined();
        expect(ctrl.networkAdminStates.UP).toBeDefined();
        expect(ctrl.networkAdminStates.DOWN).toBeDefined();
        expect(Object.keys(ctrl.networkStatuses).length).toBe(2);
      });

      it('defines a multiple-allocation table', function() {
        expect(ctrl.tableLimits).toBeDefined();
        expect(ctrl.tableLimits.maxAllocation).toBe(-1);
      });

      it('contains help text for the table', function() {
        expect(ctrl.tableHelpText).toBeDefined();
        expect(ctrl.tableHelpText.allocHelpText).toBeDefined();
        expect(ctrl.tableHelpText.availHelpText).toBeDefined();
      });

      it('uses scope to set table data', function() {
        expect(ctrl.tableDataMulti).toBeDefined();
        expect(ctrl.tableDataMulti.available).toEqual(['net-a', 'net-b']);
        expect(ctrl.tableDataMulti.allocated).toEqual(['net-a']);
        expect(ctrl.tableDataMulti.displayedAllocated).toEqual([]);
        expect(ctrl.tableDataMulti.displayedAvailable).toEqual([]);
      });
    });

  });
})();
