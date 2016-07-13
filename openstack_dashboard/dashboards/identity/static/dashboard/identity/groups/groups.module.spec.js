/**
 * Copyright 2017 SUSE Linux.
 *
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
(function () {
  'use strict';

  describe('horizon.dashboard.identity.groups', function () {
    var $scope, registry, keystone;
    var groups = {data: {items: [{id: '1234', name: 'test_group1'}]}};

    beforeEach(module('horizon.app.core.openstack-service-api'));
    beforeEach(module('horizon.dashboard.identity.groups'));
    beforeEach(module('horizon.framework'));
    beforeEach(inject(function($injector, $q, _$rootScope_) {
      $scope = _$rootScope_.$new();
      registry =
        $injector.get('horizon.framework.conf.resource-type-registry.service');
      keystone = $injector.get('horizon.app.core.openstack-service-api.keystone');
      var deferredGroups = $q.defer();
      deferredGroups.resolve(groups);
      spyOn(keystone, 'getGroups').and.returnValue(deferredGroups.promise);
    }));

    it('registers name', function() {
      expect(registry.getResourceType('OS::Keystone::Group').
        getName()).toBe("Groups");
    });

    it('should set facets for search', function () {
      var group = registry.getResourceType('OS::Keystone::Group').filterFacets
        .map(getName);
      expect(group).toContain('name');
      expect(group).toContain('id');

      function getName(x) {
        return x.name;
      }
    });

    it('should load groups', function () {
      registry.getResourceType('OS::Keystone::Group').list().then(function(responses) {
        $scope.$apply();
        expect(responses).toEqual(groups);
      });
    });
  });
})();
