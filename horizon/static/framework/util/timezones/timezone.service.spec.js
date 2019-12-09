/*
 * Copyright 2019 99Cloud Inc.
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

  describe('horizon.framework.util.timezones.service', function () {
    var service;
    beforeEach(module('horizon.framework'));
    beforeEach(inject(function($injector) {
      service = $injector.get('horizon.framework.util.timezones.service');
    }));

    it('defines the service', function() {
      expect(service).toBeDefined();
    });

    describe('get timezone offset', function () {

      it('returns +0000(UTC offset) if nothing', function () {
        function getResult(result) {
          expect(result).toBe('+0000');
        }

        service.getTimeZoneOffset().then(getResult);
      });

      it('returns the timezone offset', function() {

        function getResult(result) {
          expect(result).toBe('+0800');
        }

        service.getTimeZoneOffset('Asia/Shanghai').then(getResult);

      });
    });
  }); // end of horizon.framework.util.timezones
})();

