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

  describe('horizon.dashboard.identity.users.actions.create.service', function() {

    var $q, $scope, keystone, service, modal, policy, resourceType, toast;

    ///////////////////////

    beforeEach(module('horizon.framework'));
    beforeEach(module('horizon.app.core'));
    beforeEach(module('horizon.dashboard.identity.users'));

    beforeEach(inject(function($injector, _$rootScope_, _$q_) {
      $scope = _$rootScope_.$new();
      $q = _$q_;
      service = $injector.get('horizon.dashboard.identity.users.actions.create.service');
      toast = $injector.get('horizon.framework.widgets.toast.service');
      modal = $injector.get('horizon.framework.widgets.form.ModalFormService');
      keystone = $injector.get('horizon.app.core.openstack-service-api.keystone');
      policy = $injector.get('horizon.app.core.openstack-service-api.policy');
      resourceType = $injector.get('horizon.dashboard.identity.users.resourceType');
    }));

    it('should allow if can_edit_user is set True in OPENSTACK_KEYSTONE_BACKEND', function() {
      //for canEditUser
      var deferredCanEditUser = $q.defer();
      deferredCanEditUser.resolve(true);
      spyOn(keystone, 'canEditIdentity').and.returnValue(deferredCanEditUser.promise);

      //for ifAllowed
      var deferredIfAllowed = $q.defer();
      deferredIfAllowed.resolve(true);
      spyOn(policy, 'ifAllowed').and.returnValue(deferredIfAllowed.promise);

      var allowed = service.allowed({id: '1234'});
      $scope.$apply();

      expect(allowed).toBeTruthy();
      expect(policy.ifAllowed).toHaveBeenCalledWith(
        { rules: [['identity', 'identity:create_user']] });
    });

    it('should allow if can_edit_user is set True in OPENSTACK_KEYSTONE_BACKEND', function() {
      //for canEditUser
      var deferredCanEditUser = $q.defer();
      deferredCanEditUser.resolve(false);
      spyOn(keystone, 'canEditIdentity').and.returnValue(deferredCanEditUser.promise);

      //for ifAllowed
      var deferredIfAllowed = $q.defer();
      deferredIfAllowed.resolve(true);
      spyOn(policy, 'ifAllowed').and.returnValue(deferredIfAllowed.promise);

      var allowed = service.allowed({id: '1234'});
      $scope.$apply();

      // reject
      expect(allowed.$$state.status).toEqual(1);
    });

    it('should open the modal', function() {
      spyOn(modal, 'open').and.returnValue($q.defer().promise);
      spyOn(keystone, 'getVersion').and.returnValue($q.defer().promise);
      spyOn(keystone, 'getDefaultDomain').and.returnValue($q.defer().promise);
      spyOn(keystone, 'getProjects').and.returnValue($q.defer().promise);
      spyOn(keystone, 'getRoles').and.returnValue($q.defer().promise);

      service.perform();
      $scope.$apply();

      expect(modal.open).toHaveBeenCalled();
    });

    it('should submit create user request to keystone', function() {
      var deferred = $q.defer();
      spyOn(keystone, 'createUser').and.returnValue(deferred.promise);
      spyOn(toast, 'add').and.callFake(angular.noop);
      spyOn(keystone, 'grantRole');
      var handler = jasmine.createSpyObj('handler', ['success']);

      deferred.resolve({data: {name: 'saved', id: '12345'}});
      service.submit({model: {name: 'entered'}}).then(handler.success);

      $scope.$apply();

      expect(keystone.createUser).toHaveBeenCalledWith({name: 'entered'});
      expect(toast.add).toHaveBeenCalledWith('success', 'User saved was successfully created.');

      expect(handler.success).toHaveBeenCalled();
      var result = handler.success.calls.first().args[0];
      expect(result.created).toEqual([{type: resourceType, id: '12345'}]);
    });

  });
})();
