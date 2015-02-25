/* jshint browser: true */
(function() {
  'use strict';

  describe('hz.widget.transfer-table module', function() {
    it('should have been defined', function() {
      expect(angular.module('hz.widget.transfer-table')).toBeDefined();
    });
  });

  describe('transfer-table directive', function() {

    var $scope, $element;

    beforeEach(module('templates'));
    beforeEach(module('smart-table'));
    beforeEach(module('hz'));
    beforeEach(module('hz.widgets'));
    beforeEach(module('hz.widget.table'));
    beforeEach(module('hz.framework.bind-scope'));
    beforeEach(module('hz.widget.transfer-table'));

    describe('max 1 allocation', function() {

      beforeEach(inject(function($injector) {
        var $compile = $injector.get('$compile');
        $scope = $injector.get('$rootScope').$new();

        $scope.tableData = {
          headers: [
            { label: 'Animal', key: 'animal', priority: 1 }
          ],
          available: [
            { id: '1', animal: 'cat' },
            { id: '2', animal: 'dog' },
            { id: '3', animal: 'fish' }
          ],
          allocated: []
        };

        var markup = '<transfer-table tr-model="tableData">Test</transfer-table>';

        $element = angular.element(markup);
        $compile($element)($scope);

        $scope.$digest();
      }));

      it('should have 0 allocated rows', function() {
        expect($element.find('.transfer-allocated tr[ng-repeat-start]').length).toBe(0);
      });

      it('should have 3 available rows', function() {
        expect($element.find('.transfer-available tr[ng-repeat-start]').length).toBe(3);
      });

      it('should have 1 allocated row if first available row allocated', function() {
        $element.find('.transfer-available tbody tr:first-child button').click();
        expect($element.find('.transfer-allocated tr[ng-repeat-start]').length).toBe(1);
      });

      it('should swap allocated row one already exists', function() {
        var available = $element.find('.transfer-available tbody tr:first-child button');
        available.click();

        // After first click, should be one allocated row
        var allocated = $element.find('.transfer-allocated tr[ng-repeat-start]');
        expect(allocated.length).toBe(1);
        expect(allocated.find('td:nth-child(2)').text().trim()).toBe('cat');

        // After second click, previously allocated row swapped out for new one
        available = $element.find('.transfer-available tbody tr:first-child button');
        available.click();

        allocated = $element.find('.transfer-allocated tr[ng-repeat-start]');
        expect(allocated.length).toBe(1);
        expect(allocated.find('td:nth-child(2)').text().trim()).toBe('dog');
      });

      it('should have 0 allocated row if allocated row de-allocated', function() {
        $element.find('.transfer-allocated tr[ng-repeat-start] button').click();
        expect($element.find('.transfer-allocated tr[ng-repeat-start]').length).toBe(0);
        expect($element.find('.transfer-available tr[ng-repeat-start]').length).toBe(3);
      });

    });

    describe('max 2 allocations', function() {

      beforeEach(inject(function($injector) {
        var $compile = $injector.get('$compile');
        $scope = $injector.get('$rootScope').$new();

        $scope.tableData = {
          headers: [
            { label: 'Animal', key: 'animal', priority: 1 }
          ],
          available: [
            { id: '1', animal: 'cat' },
            { id: '2', animal: 'dog' },
            { id: '3', animal: 'fish' }
          ],
          allocated: [],
          limits: {
            maxAllocation: 2
          }
        };

        var markup = '<transfer-table tr-model="tableData"></transfer-table>';

        $element = angular.element(markup);
        $compile($element)($scope);

        $scope.$digest();
      }));

      it('should have 0 allocated rows', function() {
        expect($element.find('.transfer-allocated tr[ng-repeat-start]').length).toBe(0);
      });

      it('should have 3 available rows', function() {
        expect($element.find('.transfer-available tr[ng-repeat-start]').length).toBe(3);
      });

      it('should allow only 2 allocated rows', function() {
        $element.find('.transfer-available tbody tr:first-child button').click();
        $element.find('.transfer-available tbody tr:first-child button').click();

        var lastRow = $element.find('.transfer-available tbody tr:first-child');
        lastRow.find('.action-col button').click();

        expect($element.find('.transfer-allocated tr[ng-repeat-start]').length).toBe(2);
        expect($element.find('.transfer-available tr[ng-repeat-start]').length).toBe(1);

        // The last row should not have been added
        expect(lastRow.find('td:nth-child(2)').text().trim()).toBe('fish');
      });
    });
  });
})();