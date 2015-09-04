/*
 * (c) Copyright 2015 Hewlett-Packard Development Company, L.P.
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 * http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */
(function () {
  'use strict';

  describe('horizon.framework.widgets.charts module', function () {
    it('should be defined', function () {
      expect(angular.module('horizon.framework.widgets.charts')).toBeDefined();
    });

    describe('showKeyFilter', function () {
      var showKeyFilter;

      beforeEach(module('horizon.framework'));

      beforeEach(inject(function (_showKeyFilterFilter_) {
        showKeyFilter = _showKeyFilterFilter_;
      }));

      it('should filter keys based on hideKey attribute', function () {
        var someData = [{}, {hideKey: true}, {hideKey: false}];
        var expectedData = [{}, {hideKey: false}];
        expect(showKeyFilter(someData)).toEqual(expectedData);
      });

      it('should accept empty arrays', function () {
        expect(showKeyFilter([])).toEqual([]);
      });

    });
  });

})();
