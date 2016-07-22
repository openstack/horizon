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
    var rolesBasePath, staticUrl;

    beforeEach(module('horizon.app.core.openstack-service-api'));
    beforeEach(module('horizon.dashboard.identity'));
    beforeEach(module('horizon.framework'));
    beforeEach(inject(function($injector) {
      rolesBasePath = $injector.get('horizon.dashboard.identity.roles.basePath');
      staticUrl = $injector.get('$window').STATIC_URL;
    }));

    it('should equal to "/static/dashboard/identity/roles"', function() {
      expect(rolesBasePath).toEqual(staticUrl + 'dashboard/identity/roles/');
    });
  });
})();
