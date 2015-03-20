/* jshint globalstrict: true */
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
(function() {
  'use strict';

  describe('Launch Instance Source Step', function() {

    beforeEach(module('hz.dashboard.launch-instance'));

    describe('Filters', function() {

      describe('diskFormat', function() {

        it("returns 'FORMAT' if given 'format' in value", inject(function(diskFormatFilter) {
          expect(diskFormatFilter({disk_format: 'format'})).toBe('FORMAT');
        }));

        it("returns empty string if given null input", inject(function(diskFormatFilter) {
          expect(diskFormatFilter(null)).toBe('');
        }));

        it("returns empty string if given input without .disk_format property", inject(function(diskFormatFilter) {
          expect(diskFormatFilter({})).toBe('');
        }));

      });

    });

  });

})();

