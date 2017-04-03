/*
 * Copyright 2017 Ericsson
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

(function() {
  "use strict";

  describe('horizon.app.core.trunks', function () {
    it('should exist', function () {
      expect(angular.module('horizon.app.core.trunks')).toBeDefined();
    });
  });

  describe('loading the trunk module', function () {
    var registry;

    beforeEach(module('horizon.app.core.trunks'));
    beforeEach(inject(function($injector) {
      registry = $injector.get('horizon.framework.conf.resource-type-registry.service');
    }));

    it('registers names', function() {
      expect(registry.getResourceType('OS::Neutron::Trunk').getName()).toBe("Trunks");
    });

    it('should set facets for search', function () {
      var names = registry.getResourceType('OS::Neutron::Trunk').filterFacets
        .map(getName);
      expect(names).toContain('name');
      expect(names).toContain('port_id');
      expect(names).toContain('status');
      expect(names).toContain('admin_state_up');

      function getName(x) {
        return x.name;
      }
    });
  });

})();
