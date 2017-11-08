/*
 * Licensed under the Apache License, Version 2.0 (the "License"); you may
 * not use self file except in compliance with the License. You may obtain
 * a copy of the License at
 *
 *    http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
 * WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
 * License for the specific language governing permissions and limitations
 * under the License.
 */

(function() {
  'use strict';

  describe('horizon.app.core.keypairs.actions.delete.service', function() {

    var service, novaAPI, $scope, deferredModal;
    var deleteModalService = {
      open: function () {
        deferredModal.resolve({
          pass: [{context: {id: 'a'}}],
          fail: [{context: {id: 'b'}}]
        });
        return deferredModal.promise;
      }
    };

    ///////////////////////

    beforeEach(module('horizon.app.core'));
    beforeEach(module('horizon.app.core.keypairs'));
    beforeEach(module('horizon.framework'));
    beforeEach(module('horizon.framework.widgets.modal', function($provide) {
      $provide.value('horizon.framework.widgets.modal.deleteModalService', deleteModalService);
    }));
    beforeEach(inject(function($injector, _$rootScope_, $q) {
      $scope = _$rootScope_.$new();
      deferredModal = $q.defer();
      service = $injector.get('horizon.app.core.keypairs.actions.delete.service');
      novaAPI = $injector.get('horizon.app.core.openstack-service-api.nova');
    }));

    describe('perform method', function() {

      beforeEach(function() {
        spyOn(deleteModalService, 'open').and.callThrough();
      });

      ////////////

      it('should open the delete modal and show correct labels, single object', testSingleLabels);
      it('should open the delete modal and show correct labels, plural objects', testPluralLabels);
      it('should open the delete modal with correct entities', testEntities);
      it('should only delete keypairs that are valid', testValids);
      it('should pass in a function that deletes an keypair', testNova);
      it('should check the policy if the user is allowed to delete key pair', testAllowed);

      ////////////

      function testSingleLabels() {
        var keypairs = {name: 'Hokusai'};
        service.perform(keypairs);

        $scope.$apply();

        var labels = deleteModalService.open.calls.argsFor(0)[2].labels;
        expect(deleteModalService.open).toHaveBeenCalled();
        angular.forEach(labels, function eachLabel(label) {
          expect(label.toLowerCase()).toContain('key pair');
        });
      }

      function testPluralLabels() {
        var keypairs = [{name: 'Hokusai'}, {name: 'Utamaro'}];
        service.perform(keypairs);

        $scope.$apply();

        var labels = deleteModalService.open.calls.argsFor(0)[2].labels;
        expect(deleteModalService.open).toHaveBeenCalled();
        angular.forEach(labels, function eachLabel(label) {
          expect(label.toLowerCase()).toContain('key pairs');
        });
      }

      function testEntities() {
        var keypairs = [{name: 'Hokusai'}, {name: 'Utamaro'}, {name: 'Hiroshige'}];
        service.perform(keypairs);

        $scope.$apply();

        var entities = deleteModalService.open.calls.argsFor(0)[1];
        expect(deleteModalService.open).toHaveBeenCalled();
        expect(entities.length).toEqual(keypairs.length);
      }

      function testValids() {
        var keypairs = [{name: 'Hokusai'}, {name: 'Utamaro'}, {name: 'Hiroshige'}];
        service.perform(keypairs);

        $scope.$apply();

        var entities = deleteModalService.open.calls.argsFor(0)[1];
        expect(deleteModalService.open).toHaveBeenCalled();
        expect(entities.length).toBe(keypairs.length);
        expect(entities[0].name).toEqual('Hokusai');
        expect(entities[1].name).toEqual('Utamaro');
        expect(entities[2].name).toEqual('Hiroshige');
      }

      function testNova() {
        spyOn(novaAPI, 'deleteKeypair').and.callFake(angular.noop);
        var keypairs = [{id: 1760, name: 'Hokusai'}, {id: 1753, name: 'Utamaro'}];
        service.perform(keypairs);

        $scope.$apply();

        var contextArg = deleteModalService.open.calls.argsFor(0)[2];
        var deleteFunction = contextArg.deleteEntity;
        deleteFunction(keypairs[0].id);
        expect(novaAPI.deleteKeypair).toHaveBeenCalledWith(keypairs[0].id, true);
      }

      function testAllowed() {
        var allowed = service.allowed();
        expect(allowed).toBeTruthy();
      }
    }); // end of delete modal

  }); // end of delete

})();
