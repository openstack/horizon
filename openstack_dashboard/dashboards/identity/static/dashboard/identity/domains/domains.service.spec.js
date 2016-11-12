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

  describe('domain service', function() {
    var service, $scope, detailRoute;
    beforeEach(module('horizon.dashboard.identity.domains'));
    beforeEach(inject(function($injector) {
      service = $injector.get('horizon.dashboard.identity.domains.service');
      detailRoute = $injector.get('horizon.app.core.detailRoute');
    }));

    it("getDetailsPath creates urls using the item's ID", function() {
      var myItem = {id: "1234"};
      expect(service.getDetailsPath(myItem)).toBe(detailRoute + 'OS::Keystone::Domain/1234');
    });

    describe('listDomains', function() {
      var keystone, setting, policy;
      beforeEach(inject(function($injector) {
        keystone = $injector.get('horizon.app.core.openstack-service-api.keystone');
        setting = $injector.get('horizon.app.core.openstack-service-api.settings');
        policy = $injector.get('horizon.app.core.openstack-service-api.policy');
      }));

      it("allowed list_domain and default domain scope", inject(function($q, _$rootScope_) {
        $scope = _$rootScope_.$new();
        var deferredGetDomain = $q.defer();
        var deferredGetDomains = $q.defer();
        var deferredSetting = $q.defer();
        var deferredPolicy = $q.defer();
        spyOn(keystone, 'getDomain').and.returnValue(deferredGetDomain.promise);
        spyOn(keystone, 'getDomains').and.returnValue(deferredGetDomains.promise);
        spyOn(setting, 'getSetting').and.returnValue(deferredSetting.promise);
        spyOn(policy, 'ifAllowed').and.returnValue(deferredPolicy.promise);

        var result = service.listDomains({});

        deferredGetDomain.resolve({data: {id: 'default', name: 'Default'}});
        deferredGetDomains.resolve({data: {items: [{id: '1234', name: 'test_domain1'}]}});
        deferredSetting.resolve("Default");
        deferredPolicy.resolve({"allowed": true});

        $scope.$apply();
        expect(result.$$state.value.data.items[0].trackBy).toBe('1234');
      }));

      it("allowed list_domain and not domain scope", inject(function($q, _$rootScope_) {
        $scope = _$rootScope_.$new();
        var deferredGetDomain = $q.defer();
        var deferredSetting = $q.defer();
        var deferredPolicy = $q.defer();
        spyOn(keystone, 'getDomain').and.returnValue(deferredGetDomain.promise);
        spyOn(setting, 'getSetting').and.returnValue(deferredSetting.promise);
        spyOn(policy, 'ifAllowed').and.returnValue(deferredPolicy.promise);

        var result = service.listDomains({});

        deferredGetDomain.resolve({data: {id: '1234', name: 'test_domain1'}});
        deferredSetting.resolve("Default");
        deferredPolicy.resolve({"allowed": true});

        $scope.$apply();
        expect(result.$$state.value.data.items[0].trackBy).toBe('1234');
      }));
    });

    describe('getDomainPromise', function() {
      it("provides a promise", inject(function($q, $injector) {
        var keystone = $injector.get('horizon.app.core.openstack-service-api.keystone');
        var deferred = $q.defer();
        spyOn(keystone, 'getDomain').and.returnValue(deferred.promise);
        var result = service.getDomainPromise({});
        deferred.resolve({id: 1, name: 'test_domain'});
        expect(keystone.getDomain).toHaveBeenCalled();
        expect(result.$$state.value.name).toBe('test_domain');
      }));
    });
  });

})();
