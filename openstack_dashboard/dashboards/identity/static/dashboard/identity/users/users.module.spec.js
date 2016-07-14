/**
 * Copyright 2015 IBM Corp.
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

  describe('loading the module', function () {
    var registry;

    beforeEach(module('horizon.app.core'));
    beforeEach(module('horizon.dashboard.identity.users'));
    beforeEach(module('horizon.framework'));
    beforeEach(inject(function($injector) {
      registry = $injector.get('horizon.framework.conf.resource-type-registry.service');
    }));

    it('should set facets for search', function () {
      var names = registry.getResourceType('OS::Keystone::User').filterFacets
        .map(getName);
      expect(names).toContain('name');
      expect(names).toContain('email');
      expect(names).toContain('id');
      expect(names).toContain('enabled');

      function getName(x) {
        // underscore.js and .pluck() would be great here.
        return x.name;
      }
    });
  });
})();
