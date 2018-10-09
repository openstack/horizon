/*
 * Copyright 2016 Symantec Corp.
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

  describe('Launch Instance Server Groups Step', function() {

    describe('LaunchInstanceServerGroupsController', function() {
      var ctrl;

      beforeEach(module('horizon.dashboard.project'));

      beforeEach(inject(function($controller) {
        var model = {
          newInstanceSpec: {
            server_groups: [ 'server group 1' ]
          },
          serverGroups: [ 'server group 1', 'server group 2' ]
        };
        ctrl = $controller(
          'LaunchInstanceServerGroupsController',
          {
            launchInstanceModel: model
          });
      }));

      it('contains its table labels', function() {
        expect(ctrl.tableData).toBeDefined();
        expect(Object.keys(ctrl.tableData).length).toBeGreaterThan(0);
      });

      it('sets table data to appropriate scoped items', function() {
        expect(ctrl.tableData).toBeDefined();
        expect(Object.keys(ctrl.tableData).length).toBe(4);
        expect(ctrl.tableData.available).toEqual([ 'server group 1', 'server group 2' ]);
        expect(ctrl.tableData.allocated).toEqual([ 'server group 1' ]);
        expect(ctrl.tableData.displayedAvailable).toEqual([]);
        expect(ctrl.tableData.displayedAllocated).toEqual([]);
      });

      it('defines table help', function() {
        expect(ctrl.tableHelp).toBeDefined();
        expect(Object.keys(ctrl.tableHelp).length).toBe(2);
        expect(ctrl.tableHelp.noneAllocText).toBeDefined();
        expect(ctrl.tableHelp.availHelpText).toBeDefined();
      });

      it('allows only one allocation', function() {
        expect(ctrl.tableLimits).toBeDefined();
        expect(Object.keys(ctrl.tableLimits).length).toBe(1);
        expect(ctrl.tableLimits.maxAllocation).toBe(1);
      });
    });

  });
})();
