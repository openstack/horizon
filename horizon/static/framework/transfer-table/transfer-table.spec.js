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

  describe('hz.widget.transfer-table module', function() {
    it('should have been defined', function() {
      expect(angular.module('hz.widget.transfer-table')).toBeDefined();
    });
  });

  describe("Filters", function() {
    var filter;

    beforeEach(module('hz.widget.transfer-table'));

    describe("warningText", function() {

      beforeEach(inject(function(warningTextFilter) {
        filter = warningTextFilter;
      }));

      it('returns value if present', function() {
        expect(filter({ thing: 'stuff'}, 'thing')).toBe('stuff');
      });

      it('returns empty string if not present', function() {
        expect(filter({ thing: 'stuff'}, 'other')).toBe('');
      });

    });

    describe("rowFilter", function() {

      beforeEach(inject(function(rowFilterFilter) {
        filter = rowFilterFilter;
      }));

      it('returns item if field is falsy', function() {
        expect(filter({ hi: 'there' }, false)).toEqual({ hi: 'there' });
      });

      it('returns items only where field property is falsy', function() {
        var items = [
          {hi: 'there'},
          {},
          {hi: true},
          {hi: false}
        ];
        expect(filter(items, 'hi')).toEqual([{}, {hi: false}]);
      });

    });

    describe("foundText", function() {

      beforeEach(inject(function(foundTextFilter) {
        filter = foundTextFilter;
      }));

      it('returns expected text', function() {
        var items = [1,2,3];
        expect(filter(items, 6)).toBe('Found 3 of 6');
      });

    });

  });

  describe('transfer-table directive', function() {

    var $scope, $timeout, $element;

    beforeEach(module('templates'));
    beforeEach(module('smart-table'));
    beforeEach(module('hz'));
    beforeEach(module('hz.widgets'));
    beforeEach(module('hz.widget.action-list'));
    beforeEach(module('hz.widget.table'));
    beforeEach(module('hz.widget.transfer-table'));

    describe('max 1 allocation', function() {

      beforeEach(inject(function($injector) {
        var $compile = $injector.get('$compile');
        $scope = $injector.get('$rootScope').$new();
        $timeout = $injector.get('$timeout');

        var available = [
          { id: '1', animal: 'cat' },
          { id: '2', animal: 'dog' },
          { id: '3', animal: 'fish' }
        ];

        $scope.tableData = {
          available: available,
          allocated: [],
          displayedAvailable: [].concat(available),
          displayedAllocated: []
        };

        var markup = '<transfer-table tr-model="tableData">' +
          '<allocated>' +
          '<table st-table="tableData.displayedAllocated" st-safe-src="tableData.allocated" hz-table>' +
          '<thead><tr><th>Animal</th></tr></thead>' +
          '<tbody><tr ng-repeat="alRow in tableData.displayedAllocated">' +
          '<td>{$ alRow.animal $}</td>' +
          '<td><action-list>' +
          ' <action callback="trCtrl.deallocate" item="alRow">x' +
          ' </action>' +
          '</action-list></td>' +
          '</tr></tbody>' +
          '</table>' +
          '</allocated>' +
          '<available>' +
          '<table st-table="tableData.available" hz-table>' +
          '<thead><tr><th>Animal</th></tr></thead>' +
          '<tbody><tr ng-repeat="row in tableData.available" ng-if="!trCtrl.allocatedIds[row.id]">' +
          '<td>{$ row.animal $}</td>' +
          '<td><action-list>' +
          ' <action callback="trCtrl.allocate" item="row">x' +
          ' </action>' +
          '</action-list></td>' +
          '</tr></tbody>' +
          '</table>' +
          '</available>' +
          '</transfer-table>';

        $element = angular.element(markup);
        $compile($element)($scope);

        $scope.$digest();
      }));

      it('should have 0 allocated rows', function() {
        expect($element.find('.transfer-allocated tr[ng-repeat]').length).toBe(0);
      });

      it('should have 3 available rows', function() {
        expect($element.find('.transfer-available tr[ng-repeat]').length).toBe(3);
      });

      it('should have 1 allocated row if first available row allocated', function() {
        $element.find('.transfer-available tbody tr:first-child button').click();
        expect($element.find('.transfer-allocated tr[ng-repeat]').length).toBe(1);
      });

      it('should swap allocated row if one already exists', function() {
        var available = $element.find('.transfer-available tbody tr:first-child button');
        available.click();

        // After first click, should be one allocated row
        var allocated = $element.find('.transfer-allocated tr[ng-repeat]');
        expect(allocated.length).toBe(1);
        expect(allocated.find('td:nth-child(1)').text().trim()).toBe('cat');

        // After second click, previously allocated row swapped out for new one
        available = $element.find('.transfer-available tbody tr:first-child button');
        available.click();

        $timeout.flush();

        allocated = $element.find('.transfer-allocated tr[ng-repeat]');
        expect(allocated.length).toBe(1);
        expect(allocated.find('td:nth-child(1)').text().trim()).toBe('dog');
      });

      it('should have 0 allocated row if allocated row de-allocated', function() {
        $element.find('.transfer-allocated tr[ng-repeat] button').click();
        expect($element.find('.transfer-allocated tr[ng-repeat]').length).toBe(0);
        expect($element.find('.transfer-available tr[ng-repeat]').length).toBe(3);
      });

    });

    describe('max 2 allocations', function() {

      beforeEach(inject(function($injector) {
        var $compile = $injector.get('$compile');
        $scope = $injector.get('$rootScope').$new();

        var available = [
          { id: '1', animal: 'cat' },
          { id: '2', animal: 'dog' },
          { id: '3', animal: 'fish' }
        ];

        $scope.tableData = {
          available: available,
          allocated: [],
          displayedAvailable: [].concat(available),
          displayedAllocated: []
        };

        $scope.limits = {
          maxAllocation: 2
        };

        var markup = '<transfer-table tr-model="tableData" limits="limits">' +
          '<available>' +
          '<table st-table="tableData.available" hz-table>' +
          '<thead><tr><th>Animal</th></tr></thead>' +
          '<tbody><tr ng-repeat="row in tableData.available" ng-if="!trCtrl.allocatedIds[row.id]">' +
          '<td>{$ row.animal $}</td>' +
          '<td><action-list>' +
          ' <action callback="trCtrl.allocate" item="row">x' +
          ' </action>' +
          '</action-list></td>' +
          '</tr></tbody>' +
          '</table>' +
          '</available>' +
          '<allocated>' +
          '<table st-table="tableData.allocated" hz-table>' +
          '<thead><tr><th>Animal</th></tr></thead>' +
          '<tbody><tr ng-repeat="alRow in tableData.allocated">' +
          '<td>{$ alRow.animal $}</td>' +
          '<td><action-list>' +
          ' <action callback="trCtrl.deallocate" item="alRow">x' +
          ' </action>' +
          '</action-list></td>' +
          '</tr></tbody>' +
          '</table>' +
          '</allocated>' +
          '</transfer-table>';

        $element = angular.element(markup);
        $compile($element)($scope);

        $scope.$digest();
      }));

      it('should have 0 allocated rows', function() {
        expect($element.find('.transfer-allocated tr[ng-repeat]').length).toBe(0);
      });

      it('should have 3 available rows', function() {
        expect($element.find('.transfer-available tr[ng-repeat]').length).toBe(3);
      });

      it('should allow only 2 allocated rows', function() {
        $element.find('.transfer-available tbody tr:first-child button').click();
        $element.find('.transfer-available tbody tr:first-child button').click();

        var lastRow = $element.find('.transfer-available tbody tr:first-child');
        lastRow.find('.action-col .btn').click();

        expect($element.find('.transfer-allocated tr[ng-repeat]').length).toBe(2);
        expect($element.find('.transfer-available tr[ng-repeat]').length).toBe(1);

        // The last row should not have been added
        expect(lastRow.find('td:nth-child(1)').text().trim()).toBe('fish');
      });
    });
  });
})();
