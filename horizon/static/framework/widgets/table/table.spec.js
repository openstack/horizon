/*
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 * http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */
(function() {
  'use strict';

  describe('horizon.framework.widgets.table module', function() {
    it('should have been defined', function () {
      expect(angular.module('horizon.framework.widgets.table')).toBeDefined();
    });
  });

  describe('table directives', function () {

    var $scope, $element;

    beforeEach(module('templates'));
    beforeEach(module('smart-table'));
    beforeEach(module('horizon.framework'));

    beforeEach(inject(function($injector) {
      var $compile = $injector.get('$compile');
      var $templateCache = $injector.get('$templateCache');
      var basePath = $injector.get('horizon.framework.widgets.basePath');

      $scope = $injector.get('$rootScope').$new();

      $scope.safeFakeData = [
        { id: '1', animal: 'cat' },
        { id: '2', animal: 'dog' },
        { id: '3', animal: 'fish' }
      ];

      $scope.fakeData = [];

      var markup = $templateCache.get(basePath + 'table/table.mock.html');
      $element = angular.element(markup);
      $compile($element)($scope);

      $scope.$apply();
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
        /*eslint-disable angular/ng_controller_name */
        var hzTableCtrl = $element.controller('hzTable');
        angular.forEach($scope.safeFakeData, function(row) {
          expect(hzTableCtrl.isSelected(row)).toBe(false);
        });
        /*eslint-enable angular/ng_controller_name */
      });

      it('should update selected and numSelected when select called', function() {
        /*eslint-disable angular/ng_controller_name */
        var hzTableCtrl = $element.controller('hzTable');
        var firstRow = $scope.safeFakeData[0];
        hzTableCtrl.select(firstRow, true);
        /*eslint-enable angular/ng_controller_name */

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

      it('should have numSelected === 0 when first checkbox is clicked, then unclicked',
        function() {
          var checkbox = checkboxes.first();
          checkbox[0].checked = true;
          checkbox.triggerHandler('click');

          expect($element.scope().numSelected).toBe(1);

          checkbox[0].checked = false;
          checkbox.triggerHandler('click');

          expect($element.scope().numSelected).toBe(0);
        }
      );

      it('should have numSelected === 3 and select-all checked when all rows selected', function() {
        angular.forEach(checkboxes, function(checkbox) {
          checkbox.checked = true;
          angular.element(checkbox).triggerHandler('click');
        });

        expect($element.scope().numSelected).toBe(3);
        expect($element.find('input[hz-select-all]')[0].checked).toBe(true);
      });

      it('should have select-all unchecked when all rows selected, then one deselected',
        function() {
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
        }
      );
    });

    describe('hzSelectAll directive', function() {

      it('should not be selected if there are no rows in the table', function() {
        var selectAll = $element.find('input[hz-select-all]').first();

        $scope.safeFakeData = [];
        $scope.fakeData = [];
        $scope.$apply();

        expect(selectAll[0].checked).toBe(false);
      });

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

        /*eslint-disable angular/ng_timeout_service */
        // Wait for the slide down animation to complete before test
        setTimeout(function() {
          var summaryRow = expandIcon.closest('tr');
          expect(summaryRow.hasClass('expanded')).toBe(false);
          done();
        }, 2000);
        /*eslint-enable angular/ng_timeout_service */
      });
    });

  });

  describe('hzTableFooter directive', function () {
    var $scope, $compile, $element;

    beforeEach(module('templates'));
    beforeEach(module('horizon.framework'));

    beforeEach(inject(function ($injector) {
      $compile = $injector.get('$compile');
      $scope = $injector.get('$rootScope').$new();

      $scope.safeTableData = [
        { id: '1', animal: 'cat' },
        { id: '2', animal: 'dog' },
        { id: '3', animal: 'fish' }
      ];

      $scope.fakeTableData = [];

      var markup =
        '<table st-table="fakeTableData" st-safe-src="safeTableData" hz-table>' +
          '<tfoot hz-table-footer items="safeTableData">' +
          '</tfoot>' +
        '</table>';

      $element = angular.element(markup);
      $compile($element)($scope);
      $scope.$apply();
    }));

    it('displays the correct number of items', function() {
      expect($element).toBeDefined();
      expect($element.find('span').length).toBe(1);
      expect($element.find('span').text()).toBe('Displaying 3 items');
    });

    it('includes pagination', function() {
      expect($element.find('div').attr('st-items-by-page')).toEqual('20');
    });

  });
}());
