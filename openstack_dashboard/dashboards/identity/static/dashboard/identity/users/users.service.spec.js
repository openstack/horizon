/*
 * Copyright 2016 IBM Corp.
 *
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

  describe('Identity user service', function() {
    var service, keystone, policy, scope, settings, $q, detailRoute;

    beforeEach(module('horizon.dashboard.identity.users'));
    beforeEach(inject(function($injector, _$q_) {
      service = $injector.get('horizon.dashboard.identity.users.service');
      keystone = $injector.get('horizon.app.core.openstack-service-api.keystone');
      policy = $injector.get('horizon.app.core.openstack-service-api.policy');
      settings = $injector.get('horizon.app.core.openstack-service-api.settings');
      detailRoute = $injector.get('horizon.app.core.detailRoute');
      scope = $injector.get('$rootScope').$new();
      $q = _$q_;
    }));

    it("getDetailsPath creates proper url", function() {
      var item = {id: 614};
      expect(service.getDetailsPath(item)).toBe(detailRoute + 'OS::Keystone::User/614');
    });

    describe('getUsersPromise', function() {

      it("provides a promise", function() {
        var deferredGetUser = $q.defer();
        var deferredGetUsers = $q.defer();
        var deferredPolicy = $q.defer();
        spyOn(keystone, 'getUser').and.returnValue(deferredGetUser.promise);
        spyOn(keystone, 'getUsers').and.returnValue(deferredGetUsers.promise);
        spyOn(policy, 'ifAllowed').and.returnValue(deferredPolicy.promise);

        var result = service.getUsersPromise();
        deferredGetUser.resolve({data: {id: '1', name: 'puff'}});
        deferredGetUsers.resolve({data: {items: [{id: '1234', name: 'test_user1'}]}});
        deferredPolicy.resolve({"allowed": true});

        scope.$apply();
        expect(keystone.getUsers).toHaveBeenCalled();
        expect(result.$$state.value.data.items[0].name).toBe('test_user1');
      });
    });

    describe('getUserPromise', function() {

      it("provides a promise if keystone version undefined", function() {
        var deferredVersion = $q.defer();
        var deferredUser = $q.defer();
        spyOn(keystone, 'getVersion').and.returnValue(deferredVersion.promise);
        spyOn(keystone, 'getUser').and.returnValue(deferredUser.promise);

        service.getUserPromise(1);
        deferredVersion.resolve({data: {version: ''}});
        deferredUser.resolve({data: {id: '1', name: 'puff'}});

        scope.$apply();
        expect(keystone.getVersion).toHaveBeenCalled();
        expect(keystone.getUser).toHaveBeenCalled();
      });

      it("provides a promise if keystone version < 3", function() {
        var deferredVersion = $q.defer();
        var deferredUser = $q.defer();
        spyOn(keystone, 'getVersion').and.returnValue(deferredVersion.promise);
        spyOn(keystone, 'getUser').and.returnValue(deferredUser.promise);

        service.getUserPromise(1);
        deferredVersion.resolve({data: {version: 2}});
        deferredUser.resolve({data: {id: '1', name: 'puff'}});

        scope.$apply();
        expect(keystone.getVersion).toHaveBeenCalled();
        expect(keystone.getUser).toHaveBeenCalled();
      });

      it("provides a promise if keystone version 3", function() {
        var deferredVersion = $q.defer();
        var deferredProject = $q.defer();
        var deferredUser = $q.defer();
        var deferredDomain = $q.defer();
        spyOn(keystone, 'getVersion').and.returnValue(deferredVersion.promise);
        spyOn(keystone, 'getUser').and.returnValue(deferredUser.promise);
        spyOn(keystone, 'getProject').and.returnValue(deferredProject.promise);
        spyOn(keystone, 'getDomain').and.returnValue(deferredDomain.promise);

        var result = service.getUserPromise(1);
        deferredVersion.resolve({data: {version: 3}});
        deferredUser.resolve({data: {id: '1', name: 'puff', domain_id: 29,
          default_project_id: 26}});
        deferredProject.resolve({data: {name: 'puff_project'}});
        deferredDomain.resolve({data: {id: '1', name: 'puff_domain'}});

        scope.$apply();
        expect(keystone.getVersion).toHaveBeenCalled();
        expect(keystone.getProject).toHaveBeenCalled();
        expect(keystone.getUser).toHaveBeenCalled();
        expect(keystone.getDomain).toHaveBeenCalled();
        expect(result.$$state.value.data.project_name).toBe('puff_project');
        expect(result.$$state.value.data.domain_name).toBe('puff_domain');
      });
    });

    describe('getFilterFirstSettingPromise', function() {

      it('provides the setting value for identitty.users panel', function() {
        var deferredSetting = $q.defer();
        spyOn(settings, 'getSetting').and.returnValue(deferredSetting.promise);
        var result = service.getFilterFirstSettingPromise();
        deferredSetting.resolve({'identity.users': false});
        scope.$apply();
        expect(settings.getSetting).toHaveBeenCalled();
        expect(result.$$state.value).toBe(false);
      });

    });

  });
})();
