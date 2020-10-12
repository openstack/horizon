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
    var service, $httpBackend;
    var testData = {timezone_dict: {
      "Asia/Shanghai": "+0800",
      UTC: "+0000"
    }};

    beforeEach(module('horizon.framework'));
    beforeEach(inject(function ($injector, _$httpBackend_) {
      service = $injector.get('horizon.framework.util.timezones.service');
      $httpBackend = _$httpBackend_;
      $httpBackend.expectGET('/api/timezones/').respond(testData);
    }));

    it('defines the service', function () {
      expect(service).toBeDefined();
    });

    it('defines getTimeZones', function () {
      expect(service.getTimeZones()).toBeDefined();
    });

    describe('get timezone offset', function () {

      it('returns +0000(UTC offset) if nothing', function () {
        service.getTimeZoneOffset().then(getResult);
        function getResult(result) {
          expect(result).toBe('+0000');
        }
        $httpBackend.flush();
      });

      it('returns the timezone offset', function () {
        service.getTimeZoneOffset('Asia/Shanghai').then(getResult);
        function getResult(result) {
          expect(result).toBe('+0800');
        }
        $httpBackend.flush();
      });
    });
  }); // end of horizon.framework.util.timezones
})();

