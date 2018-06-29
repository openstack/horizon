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

  describe('horizon.dashboard.identity.users.actions.password.service', function() {

    var $q, $scope, keystone, service, modal, policy, toast, settings;

    ///////////////////////

    beforeEach(module('horizon.framework'));
    beforeEach(module('horizon.app.core'));
    beforeEach(module('horizon.dashboard.identity.users'));

    beforeEach(inject(function($injector, _$rootScope_, _$q_) {
      $scope = _$rootScope_.$new();
      $q = _$q_;
      service = $injector.get('horizon.dashboard.identity.users.actions.password.service');
      toast = $injector.get('horizon.framework.widgets.toast.service');
      modal = $injector.get('horizon.framework.widgets.form.ModalFormService');
      keystone = $injector.get('horizon.app.core.openstack-service-api.keystone');
      policy = $injector.get('horizon.app.core.openstack-service-api.policy');
      settings = $injector.get('horizon.app.core.openstack-service-api.settings');
    }));

    it('should check the policy if the user is allowed to change user password', function() {
      var deferred = $q.defer();
      spyOn(policy, 'ifAllowed').and.returnValue(deferred.promise);
      deferred.resolve({allowed: true});
      var deferredCanEdit = $q.defer();
      spyOn(keystone, 'canEditIdentity').and.returnValue(deferredCanEdit.promise);
      deferredCanEdit.resolve(true);
      var handler = jasmine.createSpyObj('handler', ['success']);

      service.allowed().then(handler.success);
      $scope.$apply();

      expect(handler.success).toHaveBeenCalled();
      var allowed = handler.success.calls.first().args[0];

      expect(allowed).toBeTruthy();
      expect(policy.ifAllowed).toHaveBeenCalledWith(
        { rules: [['identity', 'identity:update_user']] });
    });

    it('should open the modal', function() {
      spyOn(modal, 'open').and.returnValue($q.defer().promise);
      spyOn(keystone, 'getVersion').and.returnValue($q.defer().promise);
      spyOn(keystone, 'getDefaultDomain').and.returnValue($q.defer().promise);
      spyOn(keystone, 'getProjects').and.returnValue($q.defer().promise);
      spyOn(keystone, 'getRoles').and.returnValue($q.defer().promise);
      var deferred = $q.defer();
      spyOn(keystone, 'getUser').and.returnValue(deferred.promise);
      deferred.resolve({data: {name: 'saved', id: '12345'}});
      var deferredSettings = $q.defer();
      spyOn(settings, 'getSetting').and.returnValue(deferredSettings.promise);
      deferredSettings.resolve(true);

      service.perform({name: 'saved', id: '12345'});
      $scope.$apply();

      expect(modal.open).toHaveBeenCalled();
    });

    it('should submit change user password request to keystone', function() {

      var deferred = $q.defer();
      spyOn(keystone, 'editUser').and.returnValue(deferred.promise);
      deferred.resolve({data: {id: '12345', password: 'changed'}});

      spyOn(toast, 'add').and.callFake(angular.noop);

      service.submit({model: {id: '12345', password: 'changed'}});

      $scope.$apply();

      expect(keystone.editUser).toHaveBeenCalledWith({id: '12345', password: 'changed'});
      expect(toast.add)
        .toHaveBeenCalledWith('success', 'User password has been updated successfully.');
    });

    it('should call error process if failed', function() {

      var deferred = $q.defer();
      spyOn(keystone, 'editUser').and.returnValue(deferred.promise);
      deferred.reject({status: 500});

      service.submit({model: {id: '12345', password: 'changed'}});

      $scope.$apply();

      expect(keystone.editUser).toHaveBeenCalledWith({id: '12345', password: 'changed'});
    });

    it('should reopen modal if failed due to admin password incorrect', function() {

      spyOn(modal, 'open').and.returnValue($q.defer().promise);
      spyOn(keystone, 'getVersion').and.returnValue($q.defer().promise);
      spyOn(keystone, 'getDefaultDomain').and.returnValue($q.defer().promise);
      spyOn(keystone, 'getProjects').and.returnValue($q.defer().promise);
      spyOn(keystone, 'getRoles').and.returnValue($q.defer().promise);
      var deferredUser = $q.defer();
      spyOn(keystone, 'getUser').and.returnValue(deferredUser.promise);
      deferredUser.resolve({data: {name: 'saved', id: '12345'}});
      var deferredSettings = $q.defer();
      spyOn(settings, 'getSetting').and.returnValue(deferredSettings.promise);
      deferredSettings.resolve(true);
      var deferred = $q.defer();
      spyOn(keystone, 'editUser').and.returnValue(deferred.promise);
      deferred.reject({status: 400, data: "ADMIN_PASSWORD_INCORRECT"});

      service.submit({model: {id: '12345', password: 'changed', admin_password: 'incorrect'}});

      $scope.$apply();

      expect(keystone.editUser).toHaveBeenCalledWith({id: '12345', password: 'changed',
        admin_password: 'incorrect'});
    });
  });
})();
