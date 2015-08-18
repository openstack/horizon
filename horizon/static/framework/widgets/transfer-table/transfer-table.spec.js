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

  describe('horizon.framework.widgets.transfer-table module', function() {
    it('should have been defined', function() {
      expect(angular.module('horizon.framework.widgets.transfer-table')).toBeDefined();
    });
  });

  describe('transfer-table directive', function() {

    var $scope, $timeout, $element;

    beforeEach(module('templates'));
    beforeEach(module('smart-table'));
    beforeEach(module('horizon.framework'));

    describe('max 1 allocation', function() {

      beforeEach(inject(function($injector) {
        var $templateCache = $injector.get('$templateCache');
        var basePath = $injector.get('horizon.framework.widgets.basePath');
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

        var markup = $templateCache.get(basePath + 'transfer-table/transfer-table.max-1.mock.html');
        $element = angular.element(markup);
        $compile($element)($scope);

        $scope.$apply();
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
        var $templateCache = $injector.get('$templateCache');
        var basePath = $injector.get('horizon.framework.widgets.basePath');
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

        var markup = $templateCache.get(basePath + 'transfer-table/transfer-table.max-2.mock.html');

        $element = angular.element(markup);
        $compile($element)($scope);

        $scope.$apply();
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
