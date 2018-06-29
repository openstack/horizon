/**
 * Copyright 2016 Rackspace
 *
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

  describe('horizon.dashboard.identity.roles.actions.edit.service', function() {
    beforeEach(module('horizon.app.core'));
    beforeEach(module('horizon.dashboard.identity.roles'));
    beforeEach(module('horizon.framework'));

    var modalService, service, keystoneAPI, policyAPI, toast, resourceType, $q, $scope;

    beforeEach(inject(function($injector, _$q_, _$rootScope_) {
      service = $injector.get('horizon.dashboard.identity.roles.actions.edit.service');
      keystoneAPI = $injector.get('horizon.app.core.openstack-service-api.keystone');
      modalService = $injector.get('horizon.framework.widgets.form.ModalFormService');
      policyAPI = $injector.get('horizon.app.core.openstack-service-api.policy');
      toast = $injector.get('horizon.framework.widgets.toast.service');
      resourceType = $injector.get('horizon.dashboard.identity.roles.resourceType');
      $q = _$q_;
      $scope = _$rootScope_.$new();
    }));

    describe('perform', function() {
      it('should fetch the correct role', function test() {
        var deferred = $q.defer();
        deferred.resolve({id: 1, name: 'spam roll'});
        spyOn(keystoneAPI, 'getRole').and.returnValue(deferred.promise);
        spyOn(service, 'onLoad');

        service.perform({id: 2});
        $scope.$apply();

        expect(keystoneAPI.getRole).toHaveBeenCalled();
        expect(service.onLoad).toHaveBeenCalledWith({id: 1, name: 'spam roll'});
      });

      it('should open the edit modal', function test() {
        var role = {id: 1, name: 'spam roll'};
        var edited = {id: 1, name: 'egg roll'};
        var deferred = $q.defer();
        spyOn(modalService, 'open').and.returnValue(deferred.promise);
        spyOn(service, 'submit');

        deferred.resolve(edited);
        service.onLoad({data: role});
        $scope.$apply();

        expect(modalService.open).toHaveBeenCalled();
        var config = modalService.open.calls.argsFor(0)[0];
        expect(config.model).toEqual(role);
        expect(config.schema).toBeDefined();
        expect(service.submit).toHaveBeenCalledWith(edited);
      });

      it('should handle edit modal submission', function test() {
        var deferred = $q.defer();
        spyOn(keystoneAPI, 'editRole').and.returnValue(deferred.promise);
        spyOn(service, 'onSuccess');

        deferred.resolve('result');
        service.submit({model: 'model'});
        $scope.$apply();

        expect(keystoneAPI.editRole).toHaveBeenCalledWith('model');
        expect(service.onSuccess).toHaveBeenCalledWith('result');
      });

      it('should handle successful edit', function test() {
        spyOn(toast, 'add');
        var result = service.onSuccess({config: {data: {id: 2}}});

        expect(result.updated).toEqual([{type: resourceType, id: 2}]);
        expect(toast.add).toHaveBeenCalled();
      });

    });

    describe('allow method', function() {
      it('should use default policy if batch action', function test() {
        spyOn(keystoneAPI, 'canEditIdentity');
        spyOn(policyAPI, 'ifAllowed');
        service.allowed();
        expect(keystoneAPI.canEditIdentity).toHaveBeenCalled();
        expect(policyAPI.ifAllowed).toHaveBeenCalled();
      });
    }); // end of allowed

  }); // end of edit

})();
