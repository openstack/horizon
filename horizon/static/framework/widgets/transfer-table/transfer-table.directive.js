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

  /**
   * @ngdoc directive
   * @name horizon.framework.widgets.transfer-table.directive:transferTable
   * @element
   * @param {object} trModel Table data model (required)
   * @param {object} helpText Help text (optional)
   * @param {object} limits Max allocation (optional, default: 1)
   * @description
   * The `transferTable` directive generates two tables and allows the
   * transfer of rows between the two tables. Help text and maximum
   * allocation are configurable. The defaults for help text and limits
   * are described above (constants: helpContent and limits).
   *
   * The data model requires 4 arrays: allocated, displayedAllocated,
   * available, and displayedAvailable. Smart-Table requires 'displayed'
   * arrays for sorting and re-ordering.
   *
   * Data model:
   * ```
   * $scope.available = [
   *   { id: 'u1', username: 'User 1', disabled: true, warnings: { username: 'Invalid!' } },
   *   { id: 'u2', username: 'User 2', disabled: true, warningMessage: 'Invalid!' },
   *   { id: 'u3', username: 'User 3' }
   * ];
   *
   * $scope.allocated = [];
   *
   * $scope.tableData = {
   *   available: $scope.available,
   *   displayedAvailable: [].concat($scope.available),
   *   allocated: $scope.allocated,
   *   displayedAllocated: [].concat($scope.allocated)
   * };
   *
   * $scope.helpText = {
   *   availHelpText: 'Select one from the list'
   * };
   *
   * $scope.limits = {
   *   maxAllocation: -1
   * };
   * ```
   * Optional arguments for each row in table data model:
   *   disabled - disables the allocate button in available table
   *   warningMessage - the message to show in warning tooltip
   *   warnings - show warning text and icon next to value in table cell
   *
   * @restrict E
   *
   * @example
   * There are 2 examples available as a template: allocated.html.example and
   * available.html.example. The `transferTableController` methods are available
   * via `trCtrl`. For example, for allocation, use `trCtrl.allocate`.
   * ```
   * <transfer-table tr-model="tableData" help-text="helpText" limits="limits">
   *   <allocated>
   *     <table st-table="tableData.displayedAllocated"
   *       st-safe-src="tableData.allocated" hz-table>
   *       <thead>... header definition ...</thead>
   *       <tbody>
   *         <tr ng-repeat-start="row in tableData.displayedAllocated">
   *           <td>{$ row.username $}</td>
   *           ... more cell definitions
   *           <td action-col>
   *             <action-list>
   *               <action action-classes="'btn btn-sm btn-default'"
   *                 callback="trCtrl.deallocate" item="row">
   *                   <span class="fa fa-minus"></span>
   *               </action>
   *             </action-list>
   *           </td>
   *         </tr>
   *         <tr ng-repeat-end class="detail-row">
   *           <td class="detail">
   *             ... detail row definition ...
   *           </td>
   *           <td></td>
   *         </tr>
   *       </tbody>
   *     </table>
   *   </allocated>
   *   <available>
   *     <table st-table="tableData.displayedAvailable"
   *       st-safe-src="tableData.available" hz-table>
   *       <thead>... header definition ...</thead>
   *       <tbody>
   *         <tr ng-repeat-start="row in tableData.displayedAvailable">
   *           <td>{$ row.username $}</td>
   *           ... more cell definitions
   *           <td action-col>
   *             <action-list>
   *               <action action-classes="'btn btn-sm btn-default'"
   *                 callback="trCtrl.allocate" item="row">
   *                   <span class="fa fa-minus"></span>
   *               </action>
   *             </action-list>
   *           </td>
   *         </tr>
   *         <tr ng-repeat-end class="detail-row">
   *           <td class="detail">
   *             ... detail row definition ...
   *           </td>
   *         </tr>
   *       </tbody>
   *     </table>
   *   </available>
   * </transfer-table>
   * ```
   */
  angular
    .module('horizon.framework.widgets.transfer-table')
    .directive('transferTable', transferTable);

  transferTable.$inject = [ 'horizon.framework.widgets.basePath' ];

  function transferTable(path) {
    var directive = {
      controller: 'transferTableController',
      controllerAs: 'trCtrl',
      restrict: ' E',
      scope: true,
      transclude: true,
      templateUrl: path + 'transfer-table/transfer-table.html',
      link: link
    };

    return directive;

    //////////////////////

    function link(scope, element, attrs, ctrl, transclude) {
      var allocated = element.find('.transfer-allocated');
      var available = element.find('.transfer-available');

      transclude(scope, function(clone) {
        allocated.append(clone.filter('allocated'));
        available.append(clone.filter('available'));
      });
    }
  }
})();
