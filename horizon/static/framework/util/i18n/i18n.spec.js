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

  describe('horizon.framework.util.i18n', function () {
    beforeEach(module('horizon.framework'));

    describe('gettext', function () {
      var factory;

      describe('Normal operation', function () {
        beforeEach(inject(function ($injector) {
          factory = $injector.get("horizon.framework.util.i18n.gettext");
        }));

        it('defines the factory', function () {
          expect(factory).toBeDefined();
        });

        it('function returns what is given', function () {
          expect(factory("Hello")).toBe('Hello');
        });
      });

      describe("injected window.gettext", function () {
        beforeEach(module(function ($provide) {
          var $window = { gettext: function (x) {
            return x.replace(/good/, 'bad');
          }};
          $provide.value('$window', $window);
        }));

        // Get the factory by name.
        beforeEach(inject(function ($injector) {
          factory = $injector.get("horizon.framework.util.i18n.gettext");
        }));

        it('uses the window gettext when available', function () {
          // we can't spy on the window gettext due to (appropriate)
          // indirection.  But we can make sure it was called.
          expect(factory("good cop")).toBe("bad cop");
        });
      });
    });
  });
})();
