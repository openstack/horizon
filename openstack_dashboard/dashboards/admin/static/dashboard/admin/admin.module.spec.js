/**
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
  'use strict';

  describe('horizon.dashboard.admin', function() {
    var staticUrl, basePath;

    beforeEach(module('horizon.dashboard.admin'));

    beforeEach(inject(function($injector) {
      staticUrl = $injector.get('$window').STATIC_URL;
      basePath = $injector.get('horizon.dashboard.admin.basePath');
    }));

    it('should exist', function() {
      expect(angular.module('horizon.dashboard.admin')).toBeDefined();
    });

    it('should set path properly', function () {
      expect(basePath).toEqual(staticUrl + 'dashboard/admin/');
    });

  });

})();
