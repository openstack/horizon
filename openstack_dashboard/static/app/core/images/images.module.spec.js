/**
 * (c) Copyright 2016 Hewlett-Packard Development Company, L.P.
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

  describe('horizon.app.core.images', function () {
    it('should exist', function () {
      expect(angular.module('horizon.app.core.images')).toBeDefined();
    });
  });

  describe('loading the module', function () {
    var registry;

    beforeEach(module('horizon.app.core.images'));
    beforeEach(inject(function($injector) {
      registry = $injector.get('horizon.framework.conf.resource-type-registry.service');
    }));

    it('registers names', function() {
      // I don't really like testing this at this level, as in a way it's more
      // testing the registry features.  It's more complicated to mock the entire
      // registry in the way you'd basically have to in order to spy on the
      // setNames call.  It's my opinion that we shouldn't be testing for these
      // configurations as part of a module unit test, but I don't have a good
      // answer as to how one properly tests that their plugin-based system is
      // configured the way they expect it to be.
      expect(registry.getResourceType('OS::Glance::Image').getName()).toBe("Images");
    });

    it('should set facets for search', function () {
      var names = registry.getResourceType('OS::Glance::Image').filterFacets
        .map(getName);
      expect(names).toContain('name');
      expect(names).toContain('status');
      expect(names).toContain('protected');
      expect(names).toContain('disk_format');
      expect(names).toContain('size_min');
      expect(names).toContain('size_max');

      function getName(x) {
        // underscore.js and .pluck() would be great here.
        return x.name;
      }
    });
  });

  describe('horizon.app.core.images.imageFormats constant', function() {
    var imageFormats;

    beforeEach(module('horizon.app.core.images'));
    beforeEach(inject(function ($injector) {
      imageFormats = $injector.get('horizon.app.core.images.imageFormats');
    }));

    it('should be defined', function() {
      expect(Object.keys(imageFormats).length).toEqual(12);
    });
  });
})();
