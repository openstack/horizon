/*
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

  describe('horizon.framework.util.tech-debt.helper-functions', function () {
    beforeEach(function () {
      angular.mock.module('horizon.framework.util.tech-debt');
    });

    var hzUtils;
    beforeEach(function () {
      angular.mock.inject(function ($injector) {
        hzUtils = $injector.get('horizon.framework.util.tech-debt.helper-functions');
      });
    });

    describe('capitalize', function () {
      it('should capitalize the first letter of a string', function () {
        expect(hzUtils.capitalize('string to test')).toBe('String to test');
      });
    });

    describe('humanizeNumbers', function () {
      it('should add a comma every three number', function () {
        expect(hzUtils.humanizeNumbers('1234')).toBe('1,234');
        expect(hzUtils.humanizeNumbers('1234567')).toBe('1,234,567');
      });

      it('should work with string or numbers', function () {
        expect(hzUtils.humanizeNumbers('1234')).toBe('1,234');
        expect(hzUtils.humanizeNumbers(1234)).toBe('1,234');
      });

      it('should work with multiple values through a string', function () {
        expect(hzUtils.humanizeNumbers('My Total: 1234')).
          toBe('My Total: 1,234');

        expect(hzUtils.humanizeNumbers('My Total: 1234, His Total: 1234567')).
          toBe('My Total: 1,234, His Total: 1,234,567');
      });
    });

    describe('truncate', function () {
      var string = 'This will be cut';
      var ellipsis = '&hellip;';

      it('should truncate a string at a given length', function () {
        expect(hzUtils.truncate(string, 15)).
          toBe(string.slice(0, 15));
        expect(hzUtils.truncate(string, 20)).
          toBe(string);
      });

      it('should add an ellipsis if needed ', function () {
        expect(hzUtils.truncate(string, 15, true)).
          toBe(string.slice(0, 12) + ellipsis);

        expect(hzUtils.truncate(string, 20, true)).
          toBe(string);

        expect(hzUtils.truncate(string, 2, true)).
          toBe(ellipsis);
      });
    });
  });
})();
