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
    .directive('hzSelect', hzSelect);

  /**
   * @ngdoc directive
   * @name horizon.framework.widgets.table.directive:hzSelect
   * @element input type='checkbox'
   * @description
   * The `hzSelect` directive updates the checkbox selection state of
   * the specified row in the table. Assign this as an attribute to a
   * checkbox input element, passing in the row.
   *
   * @restrict A
   * @scope
   * @example
   *
   * ```
   * <tr ng-repeat="row in displayedCollection">
   *   <td>
   *     <input type='checkbox' hz-select='row'/>
   *   </td>
   * </tr>
   * ```
   *
   */
  function hzSelect() {
    var directive = {
      restrict: 'A',
      require: '^hzTable',
      scope: {
        row: '=hzSelect'
      },
      link: link
    };
    return directive;

    ////////////////////

    function link(scope, element, attrs, hzTableCtrl) {
      element.click(clickHandler);

      // select or unselect row
      function clickHandler() {
        scope.$apply(function() {
          scope.$evalAsync(function() {
            var checkedState = element.prop('checked');
            hzTableCtrl.toggleSelect(scope.row, checkedState, true);
          });
        });
      }
    }
  }
})();
