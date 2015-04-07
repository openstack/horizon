/*
 *    (c) Copyright 2015 Hewlett-Packard Development Company, L.P.
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

  describe('hz.dashboard', function () {
    it('should be defined', function () {
      expect(angular.module('hz.dashboard')).toBeDefined();
    });
  });

  describe('hz.dashboard:constant:dashboardBasePath', function () {
    var dashboardBasePath;

    beforeEach(module('hz.dashboard'));
    beforeEach(inject(function ($injector) {
      dashboardBasePath = $injector.get('dashboardBasePath');
    }));

    it('should be defined', function () {
      expect(dashboardBasePath).toBeDefined();
    });

    it('should equal to "/static/dashboard/"', function () {
      expect(dashboardBasePath).toEqual('/static/dashboard/');
    });
  });

})();
