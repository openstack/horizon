/*
 *    (c) Copyright 2015 Cisco Systems, Inc.
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
(function () {
  'use strict';

  describe('horizon.dashboard.developer', function () {
    it('should be defined', function () {
      expect(angular.module('horizon.dashboard.developer')).toBeDefined();
    });
  });

  describe('horizon.dashboard.developer.basePath constant', function () {
    var developerBasePath, staticUrl;

    beforeEach(module('horizon.dashboard.developer'));
    beforeEach(inject(function ($injector) {
      developerBasePath = $injector.get('horizon.dashboard.developer.basePath');
      staticUrl = $injector.get('$window').STATIC_URL;
    }));

    it('should be defined', function () {
      expect(developerBasePath).toBeDefined();
    });

    it('should equal to "/static/dashboard/developer/"', function () {
      expect(developerBasePath).toEqual(staticUrl + 'dashboard/developer/');
    });
  });
})();
