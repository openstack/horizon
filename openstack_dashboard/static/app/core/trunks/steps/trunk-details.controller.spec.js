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

  describe('Create Trunks Details Step', function() {
    beforeEach(module('horizon.app.core.trunks'));

    describe('TrunkDetailsController', function() {
      var $q, $timeout, scope, ctrl;

      beforeEach(inject(function(_$q_, _$timeout_, $rootScope, $controller) {
        $q = _$q_;
        $timeout = _$timeout_;
        scope = $rootScope.$new();
        scope.stepModels = {};
        var trunk = {
          admin_state_up: true,
          description: '',
          name: 'trunk1'
        };
        scope.initTrunk = trunk;
        scope.getTrunk = $q.when(trunk);

        ctrl = $controller('TrunkDetailsController', {
          $scope: scope
        });

      }));

      it('has adminstate options', function() {
        expect(ctrl.trunkAdminStateOptions).toBeDefined();
        expect(ctrl.trunkAdminStateOptions.length).toEqual(2);
      });

      it('has trunk property', function() {
        scope.getTrunk.then(function() {
          expect(ctrl.trunk).toBeDefined();
          expect(ctrl.trunk.admin_state_up).toBeDefined();
          expect(ctrl.trunk.admin_state_up).toEqual(true);
          expect(ctrl.trunk.description).toBeDefined();
          expect(ctrl.trunk.name).toBeDefined();
        });
        $timeout.flush();
      });

      it('should return with trunk', function() {
        scope.getTrunk.then(function() {
          var trunk = scope.stepModels.trunkSlices.getDetails();
          expect(trunk.name).toEqual('trunk1');
          expect(trunk.admin_state_up).toBe(true);
        });
        $timeout.flush();
      });

    });

  });
})();
