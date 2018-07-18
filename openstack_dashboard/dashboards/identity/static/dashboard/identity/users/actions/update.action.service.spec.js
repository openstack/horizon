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

  describe('horizon.dashboard.identity.users.actions.update.service', function() {

    var $q, $scope, keystone, service, modal, policy, toast;

    ///////////////////////

    beforeEach(module('horizon.framework'));
    beforeEach(module('horizon.app.core'));
    beforeEach(module('horizon.dashboard.identity.users'));

    beforeEach(inject(function($injector, _$rootScope_, _$q_) {
      $scope = _$rootScope_.$new();
      $q = _$q_;
      service = $injector.get('horizon.dashboard.identity.users.actions.update.service');
      toast = $injector.get('horizon.framework.widgets.toast.service');
      modal = $injector.get('horizon.framework.widgets.form.ModalFormService');
      keystone = $injector.get('horizon.app.core.openstack-service-api.keystone');
      policy = $injector.get('horizon.app.core.openstack-service-api.policy');
    }));

    it('should check the policy if the user is allowed to update user', function() {
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

      service.perform({name: 'saved', id: '12345'});
      $scope.$apply();

      expect(modal.open).toHaveBeenCalled();
    });

    it('should submit update user request to keystone', function() {

      var deferred = $q.defer();
      spyOn(keystone, 'editUser').and.returnValue(deferred.promise);
      deferred.resolve({data: {name: 'entered', id: '12345'}});

      spyOn(toast, 'add').and.callFake(angular.noop);

      service.submit({model: {name: 'entered', id: '12345'}});

      $scope.$apply();

      expect(keystone.editUser).toHaveBeenCalledWith({name: 'entered', id: '12345'});
      expect(toast.add).toHaveBeenCalledWith('success', 'User entered was successfully updated.');
    });

  });
})();
