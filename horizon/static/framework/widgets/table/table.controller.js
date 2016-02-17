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
    .controller('TableController', TableController);

  TableController.$inject = ['$scope'];

  /**
   * @ngdoc controller
   * @name horizon.framework.widgets.table.controller:TableController
   * @description Controller used by `hzTable`
   * Note that clearSelected is private and event driven.
   * To clear all of the selected checkboxes after an action, such as
   * delete, emit the event `hzTable:clearSelected` from your table
   * controller.
   */
  function TableController($scope) {

    var ctrl = this;
    ctrl.isSelected = isSelected;
    ctrl.select = select;

    clearSelected();

    ////////////////////

    var clearWatcher = $scope.$on('hzTable:clearSelected', clearSelected);
    $scope.$on('$destroy', function() {
      clearWatcher();
    });

    ////////////////////

    /*
     * return true if the row is selected
     */
    function isSelected(row) {
      var rowState = $scope.selected[row.id];
      return angular.isDefined(rowState) && rowState.checked;
    }

    function clearSelected() {
      /*eslint-disable angular/controller-as */
      $scope.selected = {};
      $scope.numSelected = 0;
      /*eslint-enable angular/controller-as */
    }

    /*
     * set the row selection state
     */
    function select(row, checkedState, broadcast) {
      $scope.selected[row.id] = {
        checked: checkedState,
        item: row
      };

      if (checkedState) {
        $scope.numSelected++;
      } else {
        $scope.numSelected--;
      }

      if (broadcast) {
        /*
         * should only walk down scope tree that has
         * matching event bindings
         */
        var rowObj = { row: row, checkedState: checkedState };
        $scope.$broadcast('hzTable:rowSelected', rowObj);
      }
    }
  }
})();
