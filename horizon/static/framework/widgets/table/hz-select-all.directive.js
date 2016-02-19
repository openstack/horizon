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

  angular
    .module('horizon.framework.widgets.table')
    .directive('hzSelectAll', hzSelectAll);

  /**
   * @ngdoc directive
   * @name horizon.framework.widgets.table.directive:hzSelectAll
   * @element input type='checkbox'
   * @description
   * The `hzSelectAll` directive updates the checkbox selection state of
   * every row in the table. Assign this as an attribute to a checkbox
   * input element, passing in the displayed row collection data.
   *
   * Required: Use `st-table` attribute to pass in the displayed
   * row collection and `st-safe-src` attribute to pass in the
   * safe row collection.
   *
   * Define a `ng-model` attribute on the individual row checkboxes
   * so that they will be updated when the select all checkbox is
   * clicked. The `hzTable` controller `tCtrl` provides a `selections` object
   * which stores the checked state of the row.
   *
   * @restrict A
   * @scope
   * @example
   *
   * ```
   * <thead>
   *   <th>
   *     <input type='checkbox' hz-select-all='displayedCollection'/>
   *   </th>
   * </thead>
   * <tbody>
   * <tr ng-repeat="row in displayedCollection">
   *   <td>
   *     <input type='checkbox' hz-select='row'
   *       ng-model='tCtrl.selections[row.id].checked'/>
   *   </td>
   * </tr>
   * </tbody>
   * ```
   *
   * To clear all of the selected checkboxes after an action, such as
   * delete, emit the event `hzTable:clearSelected` from your table
   * controller.
   *
   */
  function hzSelectAll() {
    var directive = {
      restrict: 'A',
      require: [ '^hzTable', '^stTable' ],
      scope: {
        rows: '=hzSelectAll'
      },
      link: link
    };
    return directive;

    ///////////////////

    function link(scope, element, attrs, ctrls) {
      var hzTableCtrl = ctrls[0];
      var stTableCtrl = ctrls[1];

      element.click(clickHandler);

      /*
       * watch the table state for changes
       * on sort, filter and pagination
       */
      var unWatchTableState = scope.$watch(function() {
        return stTableCtrl.tableState();
      },
        updateSelectAll,
        true
      );

      // watch the row length for add/removed rows
      var unWatchRowsLength = scope.$watch('rows.length', updateSelectAll);

      // watch for row selection
      var unWatchRowSelected = scope.$on('hzTable:rowSelected', updateSelectAll);

      // deregister $watch, $on on destroy
      scope.$on('$destroy', function () {
        unWatchTableState();
        unWatchRowsLength();
        unWatchRowSelected();
      });

      // select or unselect all
      function clickHandler() {
        scope.$apply(function() {
          scope.$evalAsync(function() {
            var checkedState = element.prop('checked');
            angular.forEach(scope.rows, function(row) {
              var selected = hzTableCtrl.isSelected(row);
              if (selected !== checkedState) {
                hzTableCtrl.toggleSelect(row, checkedState);
              }
            });
          });
        });
      }

      /*
       * update the select all checkbox when table
       * state changes (sort, filter, paginate)
       */
      function updateSelectAll() {
        var visibleRows = scope.rows;
        var numVisibleRows = visibleRows.length;
        var checkedCnt = visibleRows.filter(hzTableCtrl.isSelected).length;
        element.prop('checked', numVisibleRows > 0 && numVisibleRows === checkedCnt);
      }
    }
  }
})();
