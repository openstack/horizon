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

  angular
    .module('horizon.framework.widgets.transfer-table')
    .controller('transferTableController', TransferTableController);

  TransferTableController.$inject = [
    'horizon.framework.widgets.basePath',
    '$scope',
    '$timeout',
    '$parse',
    '$attrs',
    '$log',
    'horizon.framework.widgets.transfer-table.helpText',
    'horizon.framework.widgets.transfer-table.limits'
  ];

  /**
    * @ngdoc controller
    * @name horizon.framework.widgets.transfer-table.controller:transferTableController
    * @description
    * The `transferTableController` controller provides functions for allocating
    * and deallocating to and from the 'allocated' array, respectively.
    *
    * This controller can be accessed through `trCtrl`. See examples below.
    *
    * Functions and objects available:
    *
    *   allocate - add row to allocated array
    *     Provide this as callback for the allocate button
    *     <action-list>
    *       <action callback="trCtrl.allocate" item="row"></action>
    *     </action-list>
    *
    *   deallocate - remove row from allocated array
    *     Provide this as callback for the deallocate button
    *     <action-list>
    *       <action callback="trCtrl.deallocate" item="row"></action>
    *     </action-list>
    *
    *   updateAllocated - update allocated array after re-order
    *     This is needed if drag and drop re-ordering is enabled in
    *     the allocated table.
    *     <table st-table="displayedAllocated" st-safe-src="allocated"
    *       lr-drag-data="displayedAllocated"
    *       lr-drag-src="reorder" lr-drop-target="reorder"
    *       lr-drop-success="trCtrl.updateAllocated(e, item, collection)">
    *       ... table definition ...
    *     </table>
    *
    *   tooltipModel - custom warning tooltip model
    *     Use this with the allocate button (action-list)
    *     <action-list button-tooltip bt-model="trCtrl.tooltipModel">
    *       <action>...</action>
    *     </action-list>
    *
    */
  function TransferTableController(path, $scope, $timeout, $parse, $attrs, $log, helpText, limits) {
    var trModel = $parse($attrs.trModel)($scope);
    var trHelpText = $parse($attrs.helpText)($scope);
    var trLimits = $parse($attrs.limits)($scope);

    if (!angular.isArray(trModel.allocated)) {
      $log.error('Allocated is not an array as required.');
    }

    var ctrl = this;
    ctrl.allocatedIds = {};
    ctrl.available = {
      sourceItems: trModel.available,
      displayedItems: trModel.displayedAvailable
    };
    ctrl.allocated = {
      sourceItems: trModel.allocated,
      displayedItems: trModel.displayedAllocated
    };

    ctrl.allocate = allocate;
    ctrl.deallocate = deallocate;
    ctrl.toggleView = toggleView;
    ctrl.updateAllocated = updateAllocated;
    ctrl.numAllocated = numAllocated;

    ctrl.helpText = angular.extend({}, helpText, trHelpText);
    ctrl.limits = angular.extend({}, limits, trLimits);
    ctrl.numAvailable = numAvailable;
    ctrl.views = { allocated: true, available: true };

    init();

    //////////

    function init() {

      // populate the allocatedIds if allocated source given
      angular.forEach(ctrl.allocated.sourceItems, function(item) {
        ctrl.allocatedIds[item.id] = true;
      });
    }

    function allocate(item) {
      // Add to allocated only if limit not reached
      if (ctrl.limits.maxAllocation < 0 ||
          ctrl.limits.maxAllocation > ctrl.allocated.sourceItems.length) {
        ctrl.allocated.sourceItems.push(item);
        ctrl.allocatedIds[item.id] = true;
      }
      // Swap out items if only one allocation allowed
      else if (ctrl.limits.maxAllocation === 1) {
        var temp = ctrl.allocated.sourceItems.pop();
        delete ctrl.allocatedIds[temp.id];
        // When swapping out, Smart-Table $watch is
        // not detecting change so timeout is used as workaround.
        $timeout(function() {
          ctrl.allocated.sourceItems.push(item);
          ctrl.allocatedIds[item.id] = true;
          $scope.$apply();
        }, 0, false);
      }
    }

    // move item from from allocated to available
    function deallocate(item) {
      var index = ctrl.allocated.sourceItems.indexOf(item);
      if (index >= 0) {
        ctrl.allocated.sourceItems.splice(index, 1);
        delete ctrl.allocatedIds[item.id];
      }
    }

    // update allocated when users re-order via drag-and-drop
    function updateAllocated(event, item, orderedItems) {
      ctrl.allocated.sourceItems.splice(0, ctrl.allocated.sourceItems.length);
      Array.prototype.push.apply(ctrl.allocated.sourceItems, orderedItems);
    }

    /////////////

    function toggleView(view) {
      ctrl.views[view] = !ctrl.views[view];
    }

    function numAllocated() {
      return ctrl.allocated.sourceItems.length;
    }

    function numAvailable() {
      return ctrl.available.sourceItems.length - ctrl.allocated.sourceItems.length;
    }
  }

})();
