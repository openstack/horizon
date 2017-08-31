/**
 * Copyright 2016 99Cloud
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

  describe('horizon.dashboard.identity.roles', function () {
    it('should exist', function () {
      expect(angular.module('horizon.dashboard.identity.roles')).toBeDefined();
    });
  });

  describe('horizon.dashboard.identity.roles.basePath constant', function() {
    var q, rolesBasePath, staticUrl, registry, service, timeout;

    beforeEach(module('horizon.app.core.openstack-service-api'));
    beforeEach(module('horizon.dashboard.identity'));
    beforeEach(module('horizon.framework'));
    beforeEach(inject(function($q, $injector, $timeout) {
      q = $q;
      timeout = $timeout;
      rolesBasePath = $injector.get('horizon.dashboard.identity.roles.basePath');
      staticUrl = $injector.get('$window').STATIC_URL;
      registry = $injector.get('horizon.framework.conf.resource-type-registry.service');
      service = $injector.get('horizon.app.core.openstack-service-api.keystone');
    }));

    it('should equal to "/static/dashboard/identity/roles"', function() {
      expect(rolesBasePath).toEqual(staticUrl + 'dashboard/identity/roles/');
    });

    it('trackBy should change when role name changes', function() {
      var defer1 = q.defer();
      var defer2 = q.defer();
      spyOn(service, 'getRoles').and.returnValues(
        defer1.promise,
        defer2.promise
      );
      defer1.resolve(
        {data:
          {items:
            [{id: 'role-id',
              name: 'role-name-1',
              domain_id: null
      }]}});
      defer2.resolve(
        {data:
          {items:
            [{id: 'role-id',
              name: 'role-name-2',
              domain_id: null
      }]}});

      var resource = registry.getResourceType('OS::Keystone::Role');
      q.all([
        resource.list(),
        resource.list()
      ]).then(function(responses) {
        var trackBy1 = responses[0].data.items[0].trackBy;
        var trackBy2 = responses[1].data.items[0].trackBy;

        expect(trackBy1).toBeDefined();
        expect(trackBy2).toBeDefined();
        expect(trackBy1).not.toEqual(trackBy2);
      });

      timeout.flush();
    });

  });
})();
