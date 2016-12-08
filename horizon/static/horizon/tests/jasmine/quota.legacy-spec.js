/**
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

describe("Quotas (horizon.quota.js)", function() {

  describe("humanizeNumbers", function() {
    describe('When the language is changed to "Deutsch (de)"', function() {
      beforeEach(function() {
        module('horizon.app');
        inject();
        horizon.cookies.put("horizon_language", "de");
      });

      afterEach(function() {
        horizon.cookies.remove("horizon_language");
      });

      it('should add a period every three number', function () {
        expect(horizon.Quota.humanizeNumbers('1234')).toEqual('1.234');
        expect(horizon.Quota.humanizeNumbers('1234567')).toEqual('1.234.567');
      });

      it('should work string or numbers', function () {
        expect(horizon.Quota.humanizeNumbers('1234')).toEqual('1.234');
        expect(horizon.Quota.humanizeNumbers(1234)).toEqual('1.234');
      });

      it('should work with multiple values inside a string', function () {
        expect(horizon.Quota.humanizeNumbers('My Total: 1234')).toEqual('My Total: 1.234');

        expect(horizon.Quota.humanizeNumbers('My Total: 1234, His Total: 1234567')).toEqual('My Total: 1.234, His Total: 1.234.567');
      });
    });

    describe('When the language is changed to "Français (fr)"', function() {
      beforeEach(function() {
        module('horizon.app');
        inject();
        horizon.cookies.put("horizon_language", "fr");
      });

      afterEach(function() {
        horizon.cookies.remove("horizon_language");
      });

      it('should add a no-break space every three number', function () {
        expect(horizon.Quota.humanizeNumbers('1234')).toEqual('1 234');
        expect(horizon.Quota.humanizeNumbers('1234567')).toEqual('1 234 567');
      });

      it('should work string or numbers', function () {
        expect(horizon.Quota.humanizeNumbers('1234')).toEqual('1 234');
        expect(horizon.Quota.humanizeNumbers(1234)).toEqual('1 234');
      });

      it('should work with multiple values inside a string', function () {
        expect(horizon.Quota.humanizeNumbers('My Total: 1234')).toEqual('My Total: 1 234');

        expect(horizon.Quota.humanizeNumbers('My Total: 1234, His Total: 1234567')).toEqual('My Total: 1 234, His Total: 1 234 567');
      });
    });
  });

});
