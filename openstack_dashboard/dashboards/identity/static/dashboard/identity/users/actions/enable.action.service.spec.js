/**
 * Licensed under the Apache License, Version 2.0 (the "License"); you may
 * not use this file except in compliance with the License. You may obtain
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

  describe('horizon.dashboard.identity.users.actions.enable.service', function() {

    var $q, $scope, service, keystone, policy;
    var selected = {
      id: '1',
      enabled: false
    };

    beforeEach(module('horizon.app.core'));
    beforeEach(module('horizon.framework'));
    beforeEach(module('horizon.dashboard.identity.users'));

    beforeEach(inject(function($injector, _$rootScope_, _$q_) {
      $scope = _$rootScope_.$new();
      $q = _$q_;
      service = $injector.get('horizon.dashboard.identity.users.actions.enable.service');
      keystone = $injector.get('horizon.app.core.openstack-service-api.keystone');
      var deferred = $q.defer();
      spyOn(keystone, 'editUser').and.returnValue(deferred.promise);
      deferred.resolve({});
      var deferredCanEdit = $q.defer();
      spyOn(keystone, 'canEditIdentity').and.returnValue(deferredCanEdit.promise);
      deferredCanEdit.resolve(true);
      policy = $injector.get('horizon.app.core.openstack-service-api.policy');
      var allowedPromise = $q.defer();
      spyOn(policy, 'ifAllowed').and.returnValue(allowedPromise.promise);
      allowedPromise.resolve({allowed: true});
    }));

    it('should check the policy', function() {
      var allowed = service.allowed(selected);
      $scope.$apply();

      expect(allowed).toBeTruthy();
    });

    it('should call keystone.editUser', function() {
      service.perform(selected);
      $scope.$apply();

      expect(keystone.editUser).toHaveBeenCalledWith({id: selected.id, enabled: true});
    });
  });
})();
