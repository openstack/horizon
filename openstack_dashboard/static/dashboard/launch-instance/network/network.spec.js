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
(function(){
  'use strict';

  describe('Launch Instance Network Step', function() {

    describe('LaunchInstanceNetworkCtrl', function() {
      var scope, ctrl;

      beforeEach(module('hz.dashboard.launch-instance'));

      beforeEach(inject(function($controller) {
        scope = {model: {
                  newInstanceSpec: {networks: ['net-a']},
                  networks: ['net-a', 'net-b']}};
        ctrl = $controller('LaunchInstanceNetworkCtrl', {$scope:scope});
      }));

      it('has correct network statuses', function() {
        expect(scope.networkStatuses).toBeDefined();
        expect(scope.networkStatuses.ACTIVE).toBeDefined();
        expect(scope.networkStatuses.DOWN).toBeDefined();
        expect(Object.keys(scope.networkStatuses).length).toBe(2);
      });

      it('has correct network admin states', function() {
        expect(scope.networkAdminStates).toBeDefined();
        expect(scope.networkAdminStates.UP).toBeDefined();
        expect(scope.networkAdminStates.DOWN).toBeDefined();
        expect(Object.keys(scope.networkStatuses).length).toBe(2);
      });

      it('defines a multiple-allocation table', function() {
        expect(scope.tableLimits).toBeDefined();
        expect(scope.tableLimits.maxAllocation).toBe(-1);
      });

      it('contains its own labels', function() {
        expect(scope.label).toBeDefined();
        expect(Object.keys(scope.label).length).toBeGreaterThan(0);
      });

      it('contains help text for the table', function() {
        expect(scope.tableHelpText).toBeDefined();
        expect(scope.tableHelpText.allocHelpText).toBeDefined();
        expect(scope.tableHelpText.availHelpText).toBeDefined();
      });

      it('uses scope to set table data', function() {
        expect(scope.tableDataMulti).toBeDefined();
        expect(scope.tableDataMulti.available).toEqual(['net-a', 'net-b']);
        expect(scope.tableDataMulti.allocated).toEqual(['net-a']);
        expect(scope.tableDataMulti.displayedAllocated).toEqual([]);
        expect(scope.tableDataMulti.displayedAvailable).toEqual([]);
      });
    });

    describe('LaunchInstanceNetworkHelpCtrl', function() {
      var ctrl;

      beforeEach(module('hz.dashboard.launch-instance'));

      beforeEach(inject(function($controller) {
        ctrl = $controller('LaunchInstanceNetworkHelpCtrl', {});
      }));

      it('defines the title', function() {
        expect(ctrl.title).toBeDefined();
      });

      it('defines paragraphs', function() {
        expect(ctrl.paragraphs).toBeDefined();
        expect(ctrl.paragraphs.length).toBeGreaterThan(0);
      });

      it('defines the network characteristics title', function() {
        expect(ctrl.networkCharTitle).toBeDefined();
      });

      it('defines network characteristics paragraphs', function() {
        expect(ctrl.networkCharParagraphs).toBeDefined();
        expect(ctrl.networkCharParagraphs.length).toBeGreaterThan(0);
      });
    });
  });
})();
