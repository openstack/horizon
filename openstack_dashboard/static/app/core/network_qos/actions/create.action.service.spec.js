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

  describe('horizon.app.core.network_qos.actions.create.service', function() {

    var $q, $scope, neutronAPI, service, modalFormService, policyAPI, toast, resType;

    ///////////////////////

    beforeEach(module('horizon.framework'));
    beforeEach(module('horizon.app.core'));
    beforeEach(module('horizon.app.core.network_qos'));

    beforeEach(inject(function($injector, _$rootScope_, _$q_) {
      $scope = _$rootScope_.$new();
      $q = _$q_;
      service = $injector.get('horizon.app.core.network_qos.actions.create.service');
      toast = $injector.get('horizon.framework.widgets.toast.service');
      modalFormService = $injector.get('horizon.framework.widgets.form.ModalFormService');
      neutronAPI = $injector.get('horizon.app.core.openstack-service-api.neutron');
      policyAPI = $injector.get('horizon.app.core.openstack-service-api.policy');
      resType = $injector.get('horizon.app.core.network_qos.resourceType');
    }));

    it('should check if the user is allowed to create netwrok qos policy', function() {
      spyOn(policyAPI, 'ifAllowed').and.callThrough();
      var allowed = service.allowed();
      expect(allowed).toBeTruthy();
      expect(policyAPI.ifAllowed).toHaveBeenCalledWith(
        { rules: [['network', 'create_qos_policy']] });
    });

    it('should open the modal', function() {
      spyOn(modalFormService, 'open').and.returnValue($q.defer().promise);
      spyOn(neutronAPI, 'createNetworkQoSPolicy').and.returnValue($q.defer().promise);

      service.perform();
      $scope.$apply();

      expect(modalFormService.open).toHaveBeenCalled();
    });

    it('should submit create neutron qos request to neutron', function() {
      var deferred = $q.defer();
      spyOn(neutronAPI, 'createNetworkQoSPolicy').and.returnValue(deferred.promise);
      spyOn(toast, 'add').and.callFake(angular.noop);
      var handler = jasmine.createSpyObj('handler', ['success']);

      deferred.resolve({data: {name: 'qos1', id: '1'}});
      service.submit({model: {name: 'qos', description: undefined, shared: 'yes'}})
      .then(handler.success);

      $scope.$apply();

      expect(neutronAPI.createNetworkQoSPolicy).toHaveBeenCalledWith(
        {name: 'qos', description: undefined, shared: 'yes'});
      expect(toast.add).toHaveBeenCalledWith(
        'success', 'QoS Policy qos1 was successfully created.');

      expect(handler.success).toHaveBeenCalled();
      var result = handler.success.calls.first().args[0];
      expect(result.created).toEqual([{type: resType, id: '1'}]);
    });

  });
})();
