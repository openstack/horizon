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
  "use strict";

  describe('horizon.app.core.network_qos', function () {
    it('should exist', function () {
      expect(angular.module('horizon.app.core.network_qos')).toBeDefined();
    });
  });

  describe('qosService', function() {
    var service;
    beforeEach(module('horizon.app.core'));
    beforeEach(inject(function($injector) {
      service = $injector.get('horizon.app.core.network_qos.service');
    }));

    describe('getPoliciesPromise', function() {
      it("provides a promise that gets translated", inject(function($q, $injector, $timeout) {
        var neutron = $injector.get('horizon.app.core.openstack-service-api.neutron');
        var session = $injector.get('horizon.app.core.openstack-service-api.userSession');
        var deferred = $q.defer();
        var deferredSession = $q.defer();
        spyOn(neutron, 'getQoSPolicies').and.returnValue(deferred.promise);
        spyOn(session, 'get').and.returnValue(deferredSession.promise);
        var result = service.getPoliciesPromise({});
        deferredSession.resolve({});
        deferred.resolve({
          data: {
            items: [{id: 1, name: 'policy1'},{id:2}]
          }
        });
        $timeout.flush();
        expect(neutron.getQoSPolicies).toHaveBeenCalled();
        expect(result.$$state.value.data.items[0].name).toBe('policy1');
        expect(result.$$state.value.data.items[0].trackBy).toBe(1);
        //if no name given, name should be id value
        expect(result.$$state.value.data.items[1].name).toBe(2);
      }));
    });

    describe('getPolicyPromise', function() {
      it("provides a promise", inject(function($q, $injector) {
        var neutron = $injector.get('horizon.app.core.openstack-service-api.neutron');
        var deferred = $q.defer();
        spyOn(neutron, 'getQosPolicy').and.returnValue(deferred.promise);
        var result = service.getPolicyPromise({});
        deferred.resolve({data: {id: 1, name: 'policy1'}});
        expect(neutron.getQosPolicy).toHaveBeenCalled();
        expect(result.$$state.value.data.name).toBe('policy1');
      }));
    });

  });

})();
