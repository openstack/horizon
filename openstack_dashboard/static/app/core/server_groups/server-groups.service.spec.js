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
    var $q, $timeout, $window, detailRoute, nova, service;

    beforeEach(module('horizon.app.core.server_groups'));
    beforeEach(inject(function($injector) {
      $q = $injector.get('$q');
      $timeout = $injector.get('$timeout');
      $window = $injector.get('$window');
      detailRoute = $injector.get('horizon.app.core.detailRoute');
      nova = $injector.get('horizon.app.core.openstack-service-api.nova');
      service = $injector.get('horizon.app.core.server_groups.service');
    }));

    it("getDetailsPath creates urls using the item's ID", function() {
      var item = {id: '11'};
      expect(service.getDetailsPath(item)).toBe(detailRoute + 'OS::Nova::ServerGroup/11');
    });

    it("getInstanceDetailsPath creates urls using the item's ID", function() {
      $window.WEBROOT = '/dashboard/';
      var item = {id: "12"};
      expect(service.getInstanceDetailsPath(item)).toBe('/dashboard/project/instances/12/');
    });

    describe('getServerGroupPromise', function() {
      it("provides a promise when soft policies are supported", inject(function() {
        var deferred = $q.defer();
        var deferredPolicies = $q.defer();
        spyOn(nova, 'getServerGroup').and.returnValue(deferred.promise);
        spyOn(nova, 'isFeatureSupported').and.returnValue(deferredPolicies.promise);
        var result = service.getServerGroupPromise({});
        deferred.resolve({data: {id: '13', policies: ['affinity']}});
        deferredPolicies.resolve({data: true});
        $timeout.flush();

        expect(nova.getServerGroup).toHaveBeenCalled();
        expect(nova.isFeatureSupported).toHaveBeenCalled();
        expect(result.$$state.value.data.id).toBe('13');
      }));

      it("provides a promise when soft policies are not supported", inject(function() {
        var deferred = $q.defer();
        var deferredPolicies = $q.defer();
        spyOn(nova, 'getServerGroup').and.returnValue(deferred.promise);
        spyOn(nova, 'isFeatureSupported').and.returnValue(deferredPolicies.promise);
        var result = service.getServerGroupPromise({});
        deferred.resolve({data: {id: '15', policies: ['affinity']}});
        deferredPolicies.resolve({data: false});
        $timeout.flush();

        expect(nova.getServerGroup).toHaveBeenCalled();
        expect(nova.isFeatureSupported).toHaveBeenCalled();
        expect(result.$$state.value.data.id).toBe('15');
      }));
    });

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
