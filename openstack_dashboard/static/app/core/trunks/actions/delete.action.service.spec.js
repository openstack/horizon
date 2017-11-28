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

  describe('horizon.app.core.trunks.actions.delete.service', function() {

    var deleteModalService = {
      open: function () {
        deferredModal.resolve({
          pass: [{context: {id: 'a'}}],
          fail: [{context: {id: 'b'}}]
        });
        return deferredModal.promise;
      }
    };

    var neutronAPI = {
      deleteTrunk: function() {
        return;
      }
    };

    var policyAPI = {
      ifAllowed: function() {
        return {
          success: function(callback) {
            callback({allowed: true});
          },
          failure: function(callback) {
            callback({allowed: false});
          }
        };
      }
    };

    var deferred, service, $scope, deferredModal;

    ////////////

    beforeEach(module('horizon.app.core'));
    beforeEach(module('horizon.app.core.trunks'));
    beforeEach(module('horizon.framework'));

    beforeEach(module('horizon.framework.widgets.modal', function($provide) {
      $provide.value('horizon.framework.widgets.modal.deleteModalService', deleteModalService);
    }));

    beforeEach(module('horizon.app.core.openstack-service-api', function($provide) {
      $provide.value('horizon.app.core.openstack-service-api.neutron', neutronAPI);
      $provide.value('horizon.app.core.openstack-service-api.policy', policyAPI);
      spyOn(policyAPI, 'ifAllowed').and.callThrough();
    }));

    beforeEach(inject(function($injector, _$rootScope_, $q) {
      $scope = _$rootScope_.$new();
      service = $injector.get('horizon.app.core.trunks.actions.delete.service');
      deferred = $q.defer();
      deferredModal = $q.defer();
    }));

    function generateTrunk(trunkCount) {

      var trunks = [];
      var data = {
        owner: 'project',
        name: '',
        id: ''
      };

      for (var index = 0; index < trunkCount; index++) {
        var trunk = angular.copy(data);
        trunk.id = String(index);
        trunk.name = 'trunk' + index;
        trunks.push(trunk);
      }
      return trunks;
    }

    describe('perform method', function() {

      beforeEach(function() {
        spyOn(deleteModalService, 'open').and.callThrough();
      });

      ////////////

      it('should open the delete modal and show correct labels, one object',
        function testSingleObject() {
          var trunks = generateTrunk(1);
          service.perform(trunks[0]);
          $scope.$apply();

          var labels = deleteModalService.open.calls.argsFor(0)[2].labels;
          expect(deleteModalService.open).toHaveBeenCalled();
          angular.forEach(labels, function eachLabel(label) {
            expect(label.toLowerCase()).toContain('trunk');
          });
        }
      );

      it('should open the delete modal and show correct singular labels',
        function testSingleLabels() {
          var trunks = generateTrunk(1);
          service.perform(trunks);
          $scope.$apply();

          var labels = deleteModalService.open.calls.argsFor(0)[2].labels;
          expect(deleteModalService.open).toHaveBeenCalled();
          angular.forEach(labels, function eachLabel(label) {
            expect(label.toLowerCase()).toContain('trunk');
          });
        }
      );

      it('should open the delete modal and show correct plural labels',
        function testpluralLabels() {
          var trunks = generateTrunk(2);
          service.perform(trunks);
          $scope.$apply();

          var labels = deleteModalService.open.calls.argsFor(0)[2].labels;
          expect(deleteModalService.open).toHaveBeenCalled();
          angular.forEach(labels, function eachLabel(label) {
            expect(label.toLowerCase()).toContain('trunks');
          });
        }
      );

      it('should open the delete modal with correct entities',
        function testEntities() {
          var count = 3;
          var trunks = generateTrunk(count);
          service.perform(trunks);
          $scope.$apply();

          var entities = deleteModalService.open.calls.argsFor(0)[1];
          expect(deleteModalService.open).toHaveBeenCalled();
          expect(entities.length).toEqual(count);
        }
      );

      it('should only delete trunks that are valid',
        function testValids() {
          var count = 2;
          var trunks = generateTrunk(count);
          service.perform(trunks);
          $scope.$apply();

          var entities = deleteModalService.open.calls.argsFor(0)[1];
          expect(deleteModalService.open).toHaveBeenCalled();
          expect(entities.length).toBe(count);
          expect(entities[0].name).toEqual('trunk0');
          expect(entities[1].name).toEqual('trunk1');
        }
      );

      it('should pass in a function that deletes a trunk',
        function testNeutron() {
          spyOn(neutronAPI, 'deleteTrunk');
          var count = 1;
          var trunks = generateTrunk(count);
          var trunk = trunks[0];
          service.perform(trunks);
          $scope.$apply();

          var contextArg = deleteModalService.open.calls.argsFor(0)[2];
          var deleteFunction = contextArg.deleteEntity;
          deleteFunction(trunk.id);
          expect(neutronAPI.deleteTrunk).toHaveBeenCalledWith(trunk.id);
        }
      );

    }); // end of delete modal

    describe('allow method', function() {

      var resolver = {
        success: function() {},
        error: function() {}
      };

      beforeEach(function() {
        spyOn(resolver, 'success');
        spyOn(resolver, 'error');
      });

      ////////////

      it('should use default policy if batch action',
        function testBatch() {
          service.allowed();
          $scope.$apply();
          expect(policyAPI.ifAllowed).toHaveBeenCalled();
          expect(resolver.success).not.toHaveBeenCalled();
          expect(resolver.error).not.toHaveBeenCalled();
        }
      );

      it('allows delete if trunk can be deleted',
        function testValid() {
          service.allowed().success(resolver.success);
          $scope.$apply();
          expect(resolver.success).toHaveBeenCalled();
        }
      );

      it('disallows delete if trunk is not owned by user',
        function testOwner() {
          deferred.reject();
          service.allowed().failure(resolver.error);
          $scope.$apply();
          expect(resolver.error).toHaveBeenCalled();
        }
      );

    }); // end of allow method

  }); // end of delete.service

})();
