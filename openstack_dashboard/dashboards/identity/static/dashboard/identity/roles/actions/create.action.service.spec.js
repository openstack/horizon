/**
 * Copyright 2016 99Cloud
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

  describe('horizon.dashboard.identity.roles.actions.create.service', function() {

    var $q, $scope, keystoneAPI, service, modalFormService, policyAPI, resType, toast;

    ///////////////////////

    beforeEach(module('horizon.framework'));
    beforeEach(module('horizon.app.core'));
    beforeEach(module('horizon.dashboard.identity.roles'));

    beforeEach(inject(function($injector, _$rootScope_, _$q_) {
      $scope = _$rootScope_.$new();
      $q = _$q_;
      service = $injector.get('horizon.dashboard.identity.roles.actions.create.service');
      toast = $injector.get('horizon.framework.widgets.toast.service');
      modalFormService = $injector.get('horizon.framework.widgets.form.ModalFormService');
      keystoneAPI = $injector.get('horizon.app.core.openstack-service-api.keystone');
      policyAPI = $injector.get('horizon.app.core.openstack-service-api.policy');
      resType = $injector.get('horizon.dashboard.identity.roles.resourceType');
    }));

    it('should allow if can_edit_role is set True in OPENSTACK_KEYSTONE_BACKEND', function() {
      //for canEditRole
      var deferredCanEditRole = $q.defer();
      deferredCanEditRole.resolve(true);
      spyOn(keystoneAPI, 'canEditIdentity').and.returnValue(deferredCanEditRole.promise);

      //for ifAllowed
      var deferredIfAllowed = $q.defer();
      deferredIfAllowed.resolve(true);
      spyOn(policyAPI, 'ifAllowed').and.returnValue(deferredIfAllowed.promise);

      var allowed = service.allowed({id: '1234'});
      $scope.$apply();

      expect(allowed).toBeTruthy();
      expect(policyAPI.ifAllowed).toHaveBeenCalledWith(
        { rules: [['identity', 'identity:create_role']] });
    });

    it('should allow if can_edit_role is set True in OPENSTACK_KEYSTONE_BACKEND', function() {
      //for canEditRole
      var deferredCanEditRole = $q.defer();
      deferredCanEditRole.resolve(false);
      spyOn(keystoneAPI, 'canEditIdentity').and.returnValue(deferredCanEditRole.promise);

      //for ifAllowed
      var deferredIfAllowed = $q.defer();
      deferredIfAllowed.resolve(true);
      spyOn(policyAPI, 'ifAllowed').and.returnValue(deferredIfAllowed.promise);

      var allowed = service.allowed({id: '1234'});
      $scope.$apply();

      // reject
      expect(allowed.$$state.status).toEqual(1);
    });

    it('should open the modal with the correct parameters', function() {
      var deferred = $q.defer();
      spyOn(modalFormService, 'open').and.returnValue(deferred.promise);

      service.perform();

      expect(modalFormService.open).toHaveBeenCalled();

      var config = modalFormService.open.calls.mostRecent().args[0];
      expect(config.model).toBeDefined();
      expect(config.schema).toBeDefined();
      expect(config.form).toBeDefined();
    });

    it('should submit create role request to keystone', function() {
      var deferred = $q.defer();
      spyOn(keystoneAPI, 'createRole').and.returnValue(deferred.promise);
      spyOn(toast, 'add').and.callFake(angular.noop);
      var handler = jasmine.createSpyObj('handler', ['success']);

      deferred.resolve({data: {name: 'saved', id: '12345'}});
      service.submit({model: {name: 'entered'}}).then(handler.success);

      $scope.$apply();

      expect(keystoneAPI.createRole).toHaveBeenCalledWith({name: 'entered'});
      expect(toast.add).toHaveBeenCalledWith('success', 'Role saved was successfully created.');

      expect(handler.success).toHaveBeenCalled();
      var result = handler.success.calls.first().args[0];
      expect(result.created).toEqual([{type: resType, id: '12345'}]);
    });

  });
})();
