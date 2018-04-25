/*
 * (c) Copyright 2015 Hewlett-Packard Development Company, L.P.
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

  describe('hz-dynamic-table directive', function() {
    var $compile, $rootScope, $scope;

    beforeEach(module('templates'));
    beforeEach(module('smart-table'));
    beforeEach(module('horizon.framework'));
    beforeEach(module('horizon.framework.util'));
    beforeEach(module('horizon.framework.conf'));
    beforeEach(module('horizon.framework.widgets'));
    beforeEach(module('horizon.framework.widgets.magic-search'));
    beforeEach(module('horizon.framework.widgets.table'));

    beforeEach(function() {
      horizon.cookies = {
        get: function() {
          return;
        }
      };

      spyOn(horizon.cookies, 'get').and.callThrough();

    });

    beforeEach(inject(function(_$compile_, _$rootScope_) {
      $compile = _$compile_;
      $rootScope = _$rootScope_;
      $scope = $rootScope.$new();
    }));

    it("sets class when item in transition", function() {
      var config = {
        selectAll: false,
        expand: false,
        trackId: 'id',
        columns: [
          {id: 'a', title: 'A', priority: 1},
          {id: 'b', title: 'B', priority: 2}
        ]
      };
      $scope.config = config;
      $scope.tableConfig = config;
      $scope.items = [
        {
          id: 1,
          a: "a",
          b: "b"
        },
        {
          id: 2,
          a: "a",
          b: "b"
        },
        {
          id: 3,
          a: "a",
          b: "b"
        }
      ];
      $scope.itemInTransitionFunc = function(item) {
        return item.id === 1;
      };
      var element = $compile(
        "<hz-dynamic-table" +
          " config='tableConfig'" +
          " items='items'" +
          " item-in-transition-function='itemInTransitionFunc'>" +
        "</hz-dynamic-table>")($scope);
      $scope.$digest();
      // 3 items in table, only one with ID that will return true from itemInTransitionFunc
      expect(element.find("tr.warning").length).toBe(1);
    });
  });

})();
