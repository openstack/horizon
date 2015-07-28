/**
 * (c) Copyright 2015 Hewlett-Packard Development Company, L.P.
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

  describe('horizon.app.core.images.basePath constant', function () {
    var imagesBasePath, staticUrl;

    beforeEach(module('horizon.app.core'));
    beforeEach(module('horizon.app.core.images'));
    beforeEach(inject(function ($injector) {
      imagesBasePath = $injector.get('horizon.app.core.images.basePath');
      staticUrl = $injector.get('$window').STATIC_URL;
    }));

    it('should be defined', function () {
      expect(imagesBasePath).toBeDefined();
    });

    it('should equal to "/static/app/core/images/"', function () {
      expect(imagesBasePath).toEqual(staticUrl + 'app/core/images/');
    });
  });

})();
