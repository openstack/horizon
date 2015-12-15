/*
 * (c) Copyright 2015 Hewlett-Packard Development Company, L.P.
 * Copyright 2015 IBM Corp.
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
   * @restrict E
   *
   * @param {object} trModel Table data model (required)
   * @param {object} helpText Help text (optional)
   * @param {object} limits Max allocation (optional, default: 1)
   *
   * @description
   * The `transferTable` directive generates two tables and allows the
   * transfer of rows between the two tables. Help text and maximum
   * allocation are configurable. The defaults for help text and limits
   * are described above (constants: helpContent and limits).
   *
   * Refer to transfer-table.controller.js for data model description.
   * Refer to transfer-table.example.html to see it use as a directive.
   *
   * Optional arguments for each row in table data model:
   *   disabled - disables the allocate button in available table
   *   warningMessage - the message to show in warning tooltip
   *   warnings - show warning text and icon next to value in table cell
   */
  angular
    .module('horizon.framework.widgets.transfer-table')
    .directive('transferTable', transferTable);

  transferTable.$inject = [ 'horizon.framework.widgets.basePath' ];

  function transferTable(path) {
    return {
      controller: 'transferTableController',
      controllerAs: 'trCtrl',
      restrict: ' E',
      scope: true,
      transclude: true,
      templateUrl: path + 'transfer-table/transfer-table.html',
      link: link
    };

    //////////////////////

    function link(scope, element, attrs, ctrl, transclude) {
      var allocated = element.find('.transfer-allocated');
      var available = element.find('.transfer-available');
      if ('cloneContent' in attrs) {
        var allocatedScope = scope.$new();
        allocatedScope.$displayedItems = ctrl.allocated.displayedItems;
        allocatedScope.$sourceItems = ctrl.allocated.sourceItems;
        allocatedScope.$isAllocatedTable = true;
        transclude(allocatedScope, function(clone) {
          allocated.append(clone.filter('table'));
        });
        var availableScope = scope.$new();
        availableScope.$displayedItems = ctrl.available.displayedItems;
        availableScope.$sourceItems = ctrl.available.sourceItems;
        availableScope.$isAvailableTable = true;
        transclude(availableScope, function(clone) {
          available.append(clone.filter('table'));
        });
      } else {
        transclude(scope, function(clone) {
          allocated.append(clone.filter('allocated'));
          available.append(clone.filter('available'));
        });
      }
    }
  }
})();
