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
    .directive('hzTable', hzTable);

  /**
   * @ngdoc directive
   * @name horizon.framework.widgets.table.directive:hzTable
   * @element table st-table='rowCollection'
   * @description
   * The `hzTable` directive extends the Smart-Table module to provide
   * support for saving the checkbox selection state of each row in the
   * table. A default sort key can be specified to sort the table
   * initially by this key. To reverse, add default-sort-reverse='true'
   * as well.
   *
   * Required: Use `st-table` attribute to pass in the displayed
   * row collection and `st-safe-src` attribute to pass in the
   * safe row collection.
   *
   * @restrict A
   * @scope true
   * @example
   *
   * ```
   * <table st-table='displayedCollection' st-safe-src='rowCollection'
   *   hz-table default-sort="email">
   *  <thead>
   *    <tr>
   *      <th>
   *        <input type='checkbox' hz-select-all='displayedCollection'/>
   *      </th>
   *      <th>Name</th>
   *    </tr>
   *  </thead>
   *  <tbody>
   *    <tr ng-repeat="row in displayedCollection">
   *      <td>
   *        <input type='checkbox' hz-select='row'
   *          ng-model='tCtrl.selections[row.id].checked'/>
   *      </td>
   *      <td>Foo</td>
   *    </tr>
   *  </tbody>
   * </table>
   * ```
   *
   */
  function hzTable() {
    var directive = {
      restrict: 'A',
      require: 'stTable',
      scope: true,
      controller: 'TableController',
      controllerAs: 'tCtrl',
      link: link
    };
    return directive;

    ///////////////////

    function link(scope, element, attrs, stTableCtrl) {
      if (attrs.defaultSort) {
        var reverse = attrs.defaultSortReverse === 'true';
        stTableCtrl.sortBy(attrs.defaultSort, reverse);
      }
    }
  }
})();
