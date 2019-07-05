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

(function() {
  'use strict';

  describe('images details module', function() {
    var registry, resource;
    beforeEach(module('horizon.app.core.images.details'));
    beforeEach(inject(function($injector) {
      registry = $injector.get('horizon.framework.conf.resource-type-registry.service');
    }));

    it('should be loaded', function() {
      resource = registry.getResourceType('OS::Glance::Image');
      expect(resource.detailsViews[0].id).toBe('imageDetailsOverview');
    });
  });
})();
