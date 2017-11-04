/*
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

  describe('horizon.app.core.server_groups.actions.create.service', function() {

    var $q, $scope, novaAPI, service, modalFormService, policyAPI, resType, toast;

    ///////////////////////

    beforeEach(module('horizon.framework'));
    beforeEach(module('horizon.app.core'));
    beforeEach(module('horizon.app.core.server_groups'));

    beforeEach(inject(function($injector, _$rootScope_, _$q_) {
      $scope = _$rootScope_.$new();
      $q = _$q_;
      service = $injector.get('horizon.app.core.server_groups.actions.create.service');
      toast = $injector.get('horizon.framework.widgets.toast.service');
      modalFormService = $injector.get('horizon.framework.widgets.form.ModalFormService');
      novaAPI = $injector.get('horizon.app.core.openstack-service-api.nova');
      policyAPI = $injector.get('horizon.app.core.openstack-service-api.policy');
      resType = $injector.get('horizon.app.core.server_groups.resourceType');
    }));

    it('should check the policy if the user is allowed to create server group', function() {
      spyOn(policyAPI, 'ifAllowed').and.callThrough();
      var allowed = service.allowed();
      expect(allowed).toBeTruthy();
      expect(policyAPI.ifAllowed).toHaveBeenCalledWith(
        { rules: [['compute', 'os_compute_api:os-server-groups:create']] });
    });

    it('should open the modal', function() {
      spyOn(modalFormService, 'open').and.returnValue($q.defer().promise);
      spyOn(novaAPI, 'isFeatureSupported').and.returnValue($q.defer().promise);

      service.perform();
      $scope.$apply();

      expect(modalFormService.open).toHaveBeenCalled();
    });

    it('should submit create server group request to nova', function() {
      var deferred = $q.defer();
      spyOn(novaAPI, 'createServerGroup').and.returnValue(deferred.promise);
      spyOn(toast, 'add').and.callFake(angular.noop);
      var handler = jasmine.createSpyObj('handler', ['success']);

      deferred.resolve({data: {name: 'name1', id: '1'}});
      service.submit({model: {name: 'karma', policy: 'affinity'}}).then(handler.success);

      $scope.$apply();

      expect(novaAPI.createServerGroup).toHaveBeenCalledWith(
        {name: 'karma', policies: ['affinity']});
      expect(toast.add).toHaveBeenCalledWith(
        'success', 'Server Group name1 was successfully created.');

      expect(handler.success).toHaveBeenCalled();
      var result = handler.success.calls.first().args[0];
      expect(result.created).toEqual([{type: resType, id: '1'}]);
    });

  });
})();
