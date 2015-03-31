/* jshint browser: true */
(function() {
  'use strict';

  describe('hz.widget.table module', function() {
    it('should have been defined".', function () {
      expect(angular.module('hz.widget.table')).toBeDefined();
    });
  });

  describe('table directives', function () {

    var $scope, $timeout, $element;

    beforeEach(module('smart-table'));
    beforeEach(module('hz'));
    beforeEach(module('hz.widgets'));
    beforeEach(module('hz.widget.table'));

    beforeEach(inject(function($injector) {
      var $compile = $injector.get('$compile');
      $scope = $injector.get('$rootScope').$new();
      $timeout = $injector.get('$timeout');

      $scope.safeFakeData = [
        { id: '1', animal: 'cat' },
        { id: '2', animal: 'dog' },
        { id: '3', animal: 'fish' }
      ];

      $scope.fakeData = [];

      var markup =
      '<table st-table="fakeData" st-safe-src="safeFakeData" hz-table>' +
      '<thead>' +
        '<tr>' +
          '<th><input type="checkbox" hz-select-all="fakeData" ' +
                'ng-checked="numSelected === fakeData.length"/></th>' +
          '<th></th>' +
          '<th>Animal</th>' +
        '</tr>' +
      '</thead>' +
      '<tbody>' +
        '<tr ng-repeat-start="row in fakeData">' +
          '<td><input type="checkbox" ng-model="selected[row.id].checked" ' +
                'ng-change="updateSelectCount(row)"/></td>' +
          '<td><i class="fa fa-chevron-right" hz-expand-detail></i></td>' +
          '<td>{{ row.animal }}</td>' +
        '</tr>' +
        '<tr class="detail-row" ng-repeat-end>' +
          '<td class="detail" colspan="3"></td>' +
        '</tr>' +
      '</tbody>' +
      '</table>';

      $element = angular.element(markup);
      $compile($element)($scope);

      $scope.$digest();
    }));

    describe('hzTable directive', function() {

      it('should have 3 summary rows', function() {
        expect($element.find('tbody tr[ng-repeat-start]').length).toBe(3);
      });

      it('should have 3 detail rows', function() {
        expect($element.find('tbody tr.detail-row').length).toBe(3);
      });

      it('should have each checkbox initially unchecked', function() {
        var checkboxes = $element.find('tbody tr[ng-repeat-start] input[type="checkbox"]');
        angular.forEach(checkboxes, function(checkbox) {
          expect(checkbox.checked).toBe(false);
        });
      });

      it('should have numSelected === 1 when first checkbox is clicked', function() {
        var firstInput = $element.find('tbody input[type="checkbox"]').first();
        var ngModelCtrl = firstInput.controller('ngModel');
        ngModelCtrl.$setViewValue(true);

        $scope.$digest();

        expect($element.scope().numSelected).toBe(1);
      });

      it('should have numSelected === 3 and select-all checkbox checked when all rows selected', function() {
        var checkboxes = $element.find('tbody input[type="checkbox"]');
        angular.forEach(checkboxes, function(checkbox) {
          checkbox.checked = true;
          var ngModelCtrl = angular.element(checkbox).controller('ngModel');
          ngModelCtrl.$setViewValue(true);
        });

        $scope.$digest();

        expect($element.scope().numSelected).toBe(3);
        expect($element.find('thead input[hz-select-all]')[0].checked).toBe(true);
      });

    });

    describe('hzSelectAll directive', function() {

      it('should select all checkboxes if select-all checkbox checked', function() {
        var selectAll = $element.find('input[hz-select-all]').first();
        selectAll[0].checked = true;
        selectAll.triggerHandler('click');

        $timeout.flush();

        expect($element.scope().numSelected).toBe(3);
        var checkboxes = $element.find('tbody input[type="checkbox"]');
        angular.forEach(checkboxes, function(checkbox) {
          expect(checkbox.checked).toBe(true);
        });
      });

    });

    describe('hzExpandDetail directive', function() {

      it('should have summary row with class "expanded" when expanded', function() {
        var expandIcon = $element.find('i.fa').first();
        expandIcon.click();

        var summaryRow = expandIcon.closest('tr');
        expect(summaryRow.hasClass('expanded')).toBe(true);
      });

      it('should have summary row without class "expanded" when not expanded', function(done) {
        var expandIcon = $element.find('i.fa').first();

        // Click twice to mock expand and collapse
        expandIcon.click();
        expandIcon.click();

        // Wait for the slide down animation to complete before test
        setTimeout(function() {
          var summaryRow = expandIcon.closest('tr');
          expect(summaryRow.hasClass('expanded')).toBe(false);
          done();
        }, 2000);
      });

    });
  });
}());