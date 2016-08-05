/*
 *    (c) Copyright 2016 Cisco Systems
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

  describe('horizon.framework.util.uuid module', function() {
    it('should have been defined', function () {
      expect(angular.module('horizon.framework.util.uuid')).toBeDefined();
    });
  });

  describe('uuid', function () {
    var uuid;

    beforeEach(module('horizon.framework'));
    beforeEach(inject(function ($injector) {
      uuid = $injector.get('horizon.framework.util.uuid.service');
    }));

    it('should be defined', function () {
      expect(uuid).toBeDefined();
    });

    it('should generate multiple unique IDs', function() {
      var unique = [];
      var ids = [];
      var i, j, potentialUUID, uniqueLen, isUnique;

      // Generate 10 IDs
      for (i = 0; i < 10; i += 1) {
        ids.push(uuid.generate());
      }

      // Check that the IDs are unique
      // Iterate through the IDs, check that it isn't part of our unique list,
      // then append
      for (i -= 1; i >= 0; i -= 1) {
        potentialUUID = ids[i];
        isUnique = true;
        for (j = 0, uniqueLen = unique.length; j < uniqueLen; j += 1) {
          if (potentialUUID === unique[j]) {
            isUnique = false;
          }
        }
        if (isUnique) {
          unique.push(potentialUUID);
        }
      }

      // Reverse the array, because Jasmine's "toEqual" won't work otherwise.
      unique.reverse();

      expect(ids).toEqual(unique);
    });
  });
}());
