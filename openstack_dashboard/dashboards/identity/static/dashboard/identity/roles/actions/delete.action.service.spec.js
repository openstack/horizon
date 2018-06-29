/**
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

  describe('horizon.dashboard.identity.roles.actions.delete.service', function() {
    beforeEach(module('horizon.app.core'));
    beforeEach(module('horizon.dashboard.identity.roles'));
    beforeEach(module('horizon.framework'));

    var deleteModalService, $scope, service, keystoneAPI, policyAPI;

    beforeEach(inject(function($injector, _$rootScope_) {
      $scope = _$rootScope_.$new();
      service = $injector.get('horizon.dashboard.identity.roles.actions.delete.service');
      keystoneAPI = $injector.get('horizon.app.core.openstack-service-api.keystone');
      deleteModalService = $injector.get('horizon.framework.widgets.modal.deleteModalService');
      policyAPI = $injector.get('horizon.app.core.openstack-service-api.policy');
    }));

    describe('perform method', function() {
      beforeEach(function () {
        // just need for this to return something that looks like a promise but does nothing
        spyOn(deleteModalService, 'open').and.returnValue({then: angular.noop});
      });

      it('should open the modal with correct label for single entity', function test() {
        service.perform({name: 'spam'});
        var labels = deleteModalService.open.calls.argsFor(0)[2].labels;
        expect(deleteModalService.open).toHaveBeenCalled();
        angular.forEach(labels, function eachLabel(label) {
          expect(label.toLowerCase()).toContain('role');
        });
      });

      it('should open the modal with correct label for multiple entities', function test() {
        service.perform([{name: 'one'}, {name: 'two'}]);
        var labels = deleteModalService.open.calls.argsFor(0)[2].labels;
        expect(deleteModalService.open).toHaveBeenCalled();
        angular.forEach(labels, function eachLabel(label) {
          expect(label.toLowerCase()).toContain('roles');
        });
      });

      it('should open the delete modal with correct entities', function test() {
        service.perform([{name: 'one'}, {name: 'two'}]);
        var entities = deleteModalService.open.calls.argsFor(0)[1];
        expect(deleteModalService.open).toHaveBeenCalled();
        expect(entities.length).toEqual(2);
      });

      it('should pass in a function that deletes an role', function test() {
        spyOn(keystoneAPI, 'deleteRole').and.callFake(angular.noop);
        service.perform({id: 1, name: 'one'});
        var contextArg = deleteModalService.open.calls.argsFor(0)[2];
        var deleteFunction = contextArg.deleteEntity;
        deleteFunction(1);
        expect(keystoneAPI.deleteRole).toHaveBeenCalledWith(1);
      });
    });

    describe('allow method', function() {
      it('should use default policy if batch action', function test() {
        spyOn(keystoneAPI, 'canEditIdentity');
        spyOn(policyAPI, 'ifAllowed');
        service.allowed();
        $scope.$apply();
        expect(keystoneAPI.canEditIdentity).toHaveBeenCalled();
        expect(policyAPI.ifAllowed).toHaveBeenCalled();
      });
    }); // end of allowed

  }); // end of delete

})();
