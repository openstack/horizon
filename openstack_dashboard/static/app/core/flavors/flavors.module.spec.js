/**
 *
 *  Licensed under the Apache License, Version 2.0 (the "License"); you may
 *  not use this file except in compliance with the License. You may obtain
 *  a copy of the License at
 *
 *     http://www.apache.org/licenses/LICENSE-2.0
 *
 *  Unless required by applicable law or agreed to in writing, software
 *  distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
 *  WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
 *  License for the specific language governing permissions and limitations
 *  under the License.
 */

(function () {
  'use strict';

  describe('horizon.app.core.flavors', function () {
    it('should exist', function () {
      expect(angular.module('horizon.app.core.flavors')).toBeDefined();
    });
  });

  describe('loading the module', function () {
    var registry;

    beforeEach(module('horizon.app.core.flavors'));
    beforeEach(inject(function($injector) {
      registry = $injector.get('horizon.framework.conf.resource-type-registry.service');
    }));

    it('registers names', function() {
      expect(registry.getResourceType('OS::Nova::Flavor').getName()).toBe("Flavors");
    });

    it('should set facets for search', function () {
      var names = registry.getResourceType('OS::Nova::Flavor').filterFacets
        .map(getName);
      expect(names).toContain('name');
      expect(names).toContain('vcpus');
      expect(names).toContain('ram');
      expect(names).toContain('disk');
      expect(names).toContain('os-flavor-access:is_public');

      function getName(x) {
        return x.name;
      }
    });
  });

})();
