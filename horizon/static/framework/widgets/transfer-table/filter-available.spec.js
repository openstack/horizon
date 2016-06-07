/**
 * Copyright 2016, Mirantis, Inc.
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

  describe('filterAvailable filter', function () {
    var filterAvailable;
    var input = [{
      id: 'one', content: 'item1'
    }, {
      id: 'two', content: 'item2'
    }, {
      id: 'three', content: 'item3'
    }];
    var ids = {
      'two': true
    };
    var filtered = [{
      id: 'one', content: 'item1'
    }, {
      id: 'three', content: 'item3'
    }];

    beforeEach(function() {
      module('horizon.framework.widgets.transfer-table');
      module('horizon.framework.util.filters');
      inject(function(_$filter_) {
        filterAvailable = _$filter_('filterAvailable');
      });
    });

    it('is defined', function() {
      expect(filterAvailable).toBeDefined();
    });

    it('returns an empty list for empty input', function() {
      expect(filterAvailable([])).toEqual([]);
      expect(filterAvailable(undefined)).toEqual([]);
    });

    it('returns the same list if ids dictionary is empty', function() {
      expect(filterAvailable(input, {})).toEqual(input);
    });

    it('subsequent applications to the untouched output are idempotent', function() {
      var output = filterAvailable(input, {});
      expect(filterAvailable(output, {})).toBe(output);
    });

    it('id mentioned in a dictionary is removed from output', function() {
      expect(filterAvailable(input, ids)).toEqual(filtered);
    });

    it('two successive calls with same args return the same value', function() {
      var output = filterAvailable(input, ids);
      expect(filterAvailable(input, ids)).toBe(output);
    });

    it('calls on the filtered output after the second call are idempotent', function() {
      var output = filterAvailable(input, ids);
      var output2 = filterAvailable(output, ids);
      expect(output2).not.toBe(output);
      expect(filterAvailable(output2, ids)).toBe(output2);
    });

    it('third argument changes ids dictionary interpretation', function() {
      expect(filterAvailable(input, ids, 'content')).not.toEqual(filtered);
    });

    it('third argument default value is "id"', function() {
      expect(filterAvailable(input, ids, 'id')).toEqual(filtered);
    });

  });
})();
