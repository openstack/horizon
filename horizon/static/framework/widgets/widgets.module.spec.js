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

  describe('horizon.framework.widgets', function () {
    it('should be defined', function () {
      expect(angular.module('horizon.framework.widgets')).toBeDefined();
    });
  });

  describe('horizon.framework.widgets.basePath', function () {
    beforeEach(module('horizon.framework'));

    it('should be defined and set correctly', inject([
      'horizon.framework.widgets.basePath', '$window',
      function (basePath, $window) {
        expect(basePath).toBeDefined();
        expect(basePath).toBe($window.STATIC_URL + 'framework/widgets/');
      }
    ]));
  });

})();
