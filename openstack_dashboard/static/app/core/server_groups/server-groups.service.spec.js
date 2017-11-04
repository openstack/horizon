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

  describe('server groups service', function() {
    var $q, $timeout, nova, service;

    beforeEach(module('horizon.app.core.server_groups'));
    beforeEach(inject(function($injector) {
      $q = $injector.get('$q');
      $timeout = $injector.get('$timeout');
      nova = $injector.get('horizon.app.core.openstack-service-api.nova');
      service = $injector.get('horizon.app.core.server_groups.service');
    }));

    describe('getServerGroupsPromise', function() {
      it("provides a promise when soft policies are supported", inject(function() {
        var deferred = $q.defer();
        var deferredPolicies = $q.defer();
        spyOn(nova, 'getServerGroups').and.returnValue(deferred.promise);
        spyOn(nova, 'isFeatureSupported').and.returnValue(deferredPolicies.promise);
        var result = service.getServerGroupsPromise({});
        deferred.resolve({data: {items: [{id: '1', policies: ['affinity']}]}});
        deferredPolicies.resolve({data: true});
        $timeout.flush();

        expect(nova.getServerGroups).toHaveBeenCalled();
        expect(nova.isFeatureSupported).toHaveBeenCalled();
        expect(result.$$state.value.data.items[0].id).toBe('1');
      }));

      it("provides a promise when soft policies are not supported", inject(function() {
        var deferred = $q.defer();
        var deferredPolicies = $q.defer();
        spyOn(nova, 'getServerGroups').and.returnValue(deferred.promise);
        spyOn(nova, 'isFeatureSupported').and.returnValue(deferredPolicies.promise);
        var result = service.getServerGroupsPromise({});
        deferred.resolve({data: {items: [{id: '1', policies: ['affinity']}]}});
        deferredPolicies.resolve({data: false});
        $timeout.flush();

        expect(nova.getServerGroups).toHaveBeenCalled();
        expect(nova.isFeatureSupported).toHaveBeenCalled();
        expect(result.$$state.value.data.items[0].id).toBe('1');
      }));
    });
  });

})();
