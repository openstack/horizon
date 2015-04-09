/* jshint browser: true */
(function() {
  'use strict';

  describe('hz.widget.table module', function() {
    it('should have been defined', function () {
      expect(angular.module('hz.widget.table')).toBeDefined();
    });
  });

  describe('table directives', function () {

    var $scope, $element;

    beforeEach(module('smart-table'));
    beforeEach(module('hz'));
    beforeEach(module('hz.widgets'));
    beforeEach(module('hz.widget.table'));

    beforeEach(inject(function($injector) {
      var $compile = $injector.get('$compile');
      $scope = $injector.get('$rootScope').$new();

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
            '<th><input type="checkbox" hz-select-all="fakeData"/></th>' +
            '<th></th>' +
            '<th>Animal</th>' +
          '</tr>' +
        '</thead>' +
        '<tbody>' +
          '<tr ng-repeat-start="row in fakeData">' +
            '<td><input type="checkbox" hz-select="row" ' +
                  'ng-model="selected[row.id].checked"></td>' +
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
        var checkboxes = $element.find('input[hz-select]');
        angular.forEach(checkboxes, function(checkbox) {
          expect(checkbox.checked).toBe(false);
        });
      });

      it('should return false when calling isSelected for each row', function() {
        var hzTableCtrl = $element.controller('hzTable');
        angular.forEach($scope.safeFakeData, function(row) {
          expect(hzTableCtrl.isSelected(row)).toBe(false);
        });
      });

      it('should update selected and numSelected when select called', function() {
        var hzTableCtrl = $element.controller('hzTable');
        var firstRow = $scope.safeFakeData[0];
        hzTableCtrl.select(firstRow, true);

        var hzTableScope = $element.scope();
        expect(hzTableScope.selected[firstRow.id]).toBeDefined();
        expect(hzTableScope.numSelected).toBe(1);
      });

    });

    describe('hzSelect directive', function() {
      var checkboxes;

      beforeEach(function() {
        checkboxes = $element.find('input[hz-select]');
      });

      it('should have numSelected === 1 when first checkbox is clicked', function() {
        var checkbox = checkboxes.first();
        checkbox[0].checked = true;
        checkbox.triggerHandler('click');

        expect($element.scope().numSelected).toBe(1);
      });

      it('should have numSelected === 0 when first checkbox is clicked, then unclicked', function() {
        var checkbox = checkboxes.first();
        checkbox[0].checked = true;
        checkbox.triggerHandler('click');

        expect($element.scope().numSelected).toBe(1);

        checkbox[0].checked = false;
        checkbox.triggerHandler('click');

        expect($element.scope().numSelected).toBe(0);
      });

      it('should have numSelected === 3 and select-all checked when all rows selected', function() {
        angular.forEach(checkboxes, function(checkbox) {
          checkbox.checked = true;
          angular.element(checkbox).triggerHandler('click');
        });

        expect($element.scope().numSelected).toBe(3);
        expect($element.find('input[hz-select-all]')[0].checked).toBe(true);
      });

      it('should have select-all unchecked when all rows selected, then one deselected', function() {
        angular.forEach(checkboxes, function(checkbox) {
          checkbox.checked = true;
          angular.element(checkbox).triggerHandler('click');
        });

        // all checkboxes selected so check-all should be checked
        expect($element.scope().numSelected).toBe(3);
        expect($element.find('input[hz-select-all]')[0].checked).toBe(true);

        // deselect one checkbox
        var firstCheckbox = checkboxes.first();
        firstCheckbox[0].checked = false;
        firstCheckbox.triggerHandler('click');

        // check-all should be unchecked
        expect($element.scope().numSelected).toBe(2);
        expect($element.find('input[hz-select-all]')[0].checked).toBe(false);
      });

    });

    describe('hzSelectAll directive', function() {

      it('should select all checkboxes if select-all checked', function() {
        var selectAll = $element.find('input[hz-select-all]').first();
        selectAll[0].checked = true;
        selectAll.triggerHandler('click');

        expect($element.scope().numSelected).toBe(3);
        var checkboxes = $element.find('tbody input[hz-select]');
        angular.forEach(checkboxes, function(checkbox) {
          expect(checkbox.checked).toBe(true);
        });
      });

      it('should deselect all checkboxes if select-all checked, then unchecked', function() {
        var selectAll = $element.find('input[hz-select-all]').first();
        selectAll[0].checked = true;
        selectAll.triggerHandler('click');

        var checkboxes = $element.find('tbody input[hz-select]');

        expect($element.scope().numSelected).toBe(3);
        angular.forEach(checkboxes, function(checkbox) {
          expect(checkbox.checked).toBe(true);
        });

        selectAll[0].checked = false;
        selectAll.triggerHandler('click');

        expect($element.scope().numSelected).toBe(0);
        angular.forEach(checkboxes, function(checkbox) {
          expect(checkbox.checked).toBe(false);
        });
      });

      it('should select all checkboxes if select-all checked with one row selected', function() {
        // select the first checkbox
        var checkbox = $element.find('input[hz-select]').first();
        checkbox[0].checked = true;
        checkbox.triggerHandler('click');

        // now click select-all checkbox
        var selectAll = $element.find('input[hz-select-all]').first();
        selectAll[0].checked = true;
        selectAll.triggerHandler('click');

        expect($element.scope().numSelected).toBe(3);
        var checkboxes = $element.find('tbody input[hz-select]');
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