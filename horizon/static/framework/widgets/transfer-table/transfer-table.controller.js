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

  angular
    .module('horizon.framework.widgets.transfer-table')
    .controller('transferTableController', TransferTableController);

  TransferTableController.$inject = [
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
    * This controller can be accessed through `trCtrl`.
    *
    * The data model assumes four arrays: allocated, displayedAllocated,
    * available, and displayedAvailable. Smart-Table requires additional
    * 'displayed' arrays for sorting and re-ordering. Of these four arrays, only
    * allocated is required. The remaining arrays are populated for you if they
    * are not present.
    *
    * @example
    * ```
    * var availableItems = [
    *   { id: 'u1', username: 'User 1', disabled: true, warnings: { username: 'Invalid!' } },
    *   { id: 'u2', username: 'User 2', disabled: true, warningMessage: 'Invalid!' },
    *   { id: 'u3', username: 'User 3' }
    * ];
    * $scope.model = { available: availableItems };
    * $scope.limits = { maxAllocation: -1 };
    * ```
    * For usage example, see the transfer-table.example.html file.
    */
  function TransferTableController($scope, $timeout, $parse, $attrs, $log, helpText, limits) {

    var trModel = $parse($attrs.trModel)($scope);
    var trHelpText = $parse($attrs.helpText)($scope);
    var trLimits = $parse($attrs.limits)($scope);

    var ctrl = this;
    ctrl.allocate = allocate;
    ctrl.deallocate = deallocate;
    ctrl.toggleView = toggleView;
    ctrl.updateAllocated = updateAllocated;
    ctrl.numAllocated = numAllocated;

    ctrl.helpText = angular.extend({}, helpText, trHelpText);
    ctrl.limits = angular.extend({}, limits, trLimits);
    ctrl.numAvailable = numAvailable;
    ctrl.views = { allocated: true, available: true };

    init(trModel);

    //////////

    function init(model) {

      if (!angular.isArray(model.available)) {
        $log.error('Available is not an array.');
      }

      if (model.allocated && !angular.isArray(model.allocated)) {
        $log.error('Allocated is not an array.');
      }

      ctrl.available = {
        sourceItems: model.available,
        displayedItems: model.displayedAvailable ? model.displayedAvailable : []
      };
      ctrl.allocated = {
        sourceItems: model.allocated ? model.allocated : [],
        displayedItems: model.displayedAllocated ? model.displayedAllocated : []
      };

      ctrl.allocatedIds = {};
      markAllocatedItems();

      $scope.$watchCollection(getAllocated, markAllocatedItems);
    }

    function getAllocated() {
      return ctrl.allocated.sourceItems;
    }

    function markAllocatedItems() {
      angular.forEach(ctrl.allocated.sourceItems, function flag(item) {
        ctrl.allocatedIds[item.id] = true;
      });
    }

    function allocate(item) {

      // we currently don't have to check for item uniqueness
      // because we are using the ng-repeat track by

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
