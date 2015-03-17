(function() {
  'use strict';

  /**
   * @ngdoc overview
   * @name hz.widget.transfer-table
   * @description
   *
   * # hz.widget.transfer-table
   *
   * The `hz.widget.transfer-table` module provides support for transferring
   * rows between two tables (allocated and available).
   *
   * Requires {@link hz.widget.table.directive:hzTable `hzTable`} module to
   * be installed.
   *
   * | Directives                                                               |
   * |--------------------------------------------------------------------------|
   * | {@link hz.widget.transfer-table.directive:transferTable `transferTable`} |
   *
   */
  angular.module('hz.widget.transfer-table', [ 'ui.bootstrap' ])

    /**
     * @ngdoc parameters
     * @name hz.widget.transfer-table.constant:helpText
     * @param {string} allocTitle Title for allocation section
     * @param {string} availTitle Title for available section
     * @param {string} availHelpText Help text shown in available section
     * @param {string} noneAllocText Text shown if no allocated items
     * @param {string} noneAvailText Text shown if no available items
     * @param {string} allocHiddenText Text shown if allocated section hidden
     * @param {string} availHiddenText Text shown if available section hidden
     * @param {string} sectionToggleText Title for section toggle chevron icon
     * @param {string} orderText Title for drag and drop re-order icon
     * @param {string} expandDetailsText Title for expand icon
     */
    .constant('helpText', {
      allocTitle: gettext('Allocated'),
      availTitle: gettext('Available'),
      availHelpText: gettext('Select one'),
      noneAllocText: gettext('Select an item from Available items below'),
      noneAvailText: gettext('No available items'),
      allocHiddenText: gettext('Expand to see allocated items'),
      availHiddenText: gettext('Expand to see available items'),
      sectionToggleText: gettext('Click to show or hide'),
      orderText: gettext('Re-order items using drag and drop'),
      expandDetailsText: gettext('Click to see more details')
    })

    /**
     * @ngdoc parameters
     * @name hz.widget.transfer-table.constant:limits
     * @param {number} maxAllocation Maximum allocation allowed
     */
    .constant('limits', {
      maxAllocation: 1
    })

    /*
     * @ngdoc filter
     * @name hz.widget.transfer-table.filter:warningText
     * @returns {string} Warning text if exists or empty string
     */
    .filter('warningText', function() {
      return function(input, key) {
        if (input && input.hasOwnProperty(key)) {
          return input[key];
        }
        return '';
      };
    })

    /**
     * @ngdoc filter
     * @name hz.widget.transfer-table.filter:rowFilter
     * @returns {array} List of filtered items based on field passed in
     */
    .filter('rowFilter', function() {
      return function(items, field) {
        if (field) {
          return items.filter(function(item) {
            return !item[field];
          });
        } else {
          return items;
        }
      };
    })

    /**
     * @ngdoc filter
     * @name hz.widget.transfer-table.filter:foundText
     * @returns {string} Help text for filter results
     */
    .filter('foundText', function() {
      return function(foundItems, total) {
        var numFound = foundItems.length;
        var transObj = { found: numFound, total: total };
        var message = gettext('Found %(found)s of %(total)s');
        return interpolate(message, transObj, true);
      };
    })

    /**
     * @ngdoc controller
     * @name hz.widget.transfer-table.controller:transferTableCtrl
     * @description
     * The `transferTableCtrl` controller provides functions for allocating
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
    .controller('transferTableCtrl',
      [ 'basePath', '$scope', '$timeout', '$parse', '$attrs', 'helpText', 'limits',
      function(path, $scope, $timeout, $parse, $attrs, helpText, limits) {
        var trModel = $parse($attrs.trModel)($scope);
        var trHelpText = $parse($attrs.helpText)($scope);
        var trLimits = $parse($attrs.limits)($scope);

        if (!angular.isArray(trModel.allocated)) {
          console.error('Allocated is not an array as required.');
        }

        var model = this;
        model.helpText = angular.extend({}, helpText, trHelpText);
        model.limits = angular.extend({}, limits, trLimits);
        model.numAvailable = trModel.available ? trModel.available.length : 0;
        model.views = { allocated: true, available: true };

        // Tooltip model
        model.tooltipModel = {
          templateUrl: path + 'action-list/warning-tooltip.html',
          data: {
            clickMessage: gettext('Click here to expand the row and view the errors.'),
            expandDetail: function() {
              var row = this.element.closest('tr');
              if (!row.hasClass('expanded')) {
                // Timeout needed to prevent
                // $apply already in progress error
                $timeout(function() {
                  row.find('[hz-expand-detail]').click();
                }, 0, false);
              }
            }
          }
        };

        function setAllocatedIds(allocatedRows) {
          model.allocatedIds = {};
          if (allocatedRows) {
            angular.forEach(allocatedRows, function(alloc) {
              model.allocatedIds[alloc.id] = true;
            });

            if (trModel.available) {
              model.numAvailable = trModel.available.length - allocatedRows.length;
            } else {
              model.numAvailable = 0;
            }
          } else {
            trModel.allocated = [];
            trModel.displayedAllocated = [];
          }
        }

        // Update tracking of allocated IDs when allocated changed
        $scope.$watchCollection(function() {
          return trModel.allocated;
        }, function(newAllocated) {
          setAllocatedIds(newAllocated);
        });

        // Update available count when available changed
        $scope.$watchCollection(function() {
          return trModel.available;
        }, function(newAvailable) {
          var numAvailable = newAvailable ? newAvailable.length : 0;
          var numAllocated = trModel.allocated ? trModel.allocated.length : 0;
          model.numAvailable = numAvailable - numAllocated;
        });

        // Initialize tracking of allocated IDs
        setAllocatedIds(trModel.allocated);

        model.allocate = function(row) {
          if (model.limits.maxAllocation < 0 ||
              trModel.allocated.length < model.limits.maxAllocation) {
            // Add to allocated only if limit not reached
            trModel.allocated.push(row);

            model.numAvailable -= 1;
          } else if (model.limits.maxAllocation === 1) {
            // Swap out rows if only one allocation allowed
            trModel.allocated.pop();

            // When swapping out, Smart-Table $watch is
            // not detecting change so timeout is used
            // as workaround.
            $timeout(function() {
              trModel.allocated.push(row);
              $scope.$apply();
            }, 0, false);
          }
        };

        model.deallocate = function(row) {
          model.numAvailable += 1;

          var allocLen = trModel.allocated.length;
          for (var i = allocLen - 1; i >= 0; i--) {
            if (trModel.allocated[i].id === row.id) {
              trModel.allocated.splice(i, 1);
            }
          }
        };

        // Show/hide allocated or available sections
        model.toggleView = function(view) {
          var show = model.views[view];
          model.views[view] = !show;
        };

        // Allocated array needs to be updated when rows re-ordered
        model.updateAllocated = function(e, item, orderedItems) {
          var allocLen = trModel.allocated.length;
          trModel.allocated.splice(0, allocLen);
          Array.prototype.push.apply(trModel.allocated, orderedItems);
        };

        model.numAllocated = function() {
          return trModel.allocated ? trModel.allocated.length : 0;
        };

        model.numDisplayedAvailable = function() {
          if (trModel.displayedAvailable) {
            var filtered = trModel.displayedAvailable.filter(function(avail) {
              return !model.allocatedIds[avail.id];
            });

            return filtered.length;
          }
          return 0;
        };
      }]
    )

    /**
     * @ngdoc directive
     * @name hz.widget.transfer-table.directive:transferTable
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
     * available.html.example. The `transferTableCtrl` methods are available
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
    .directive('transferTable', [ 'basePath',
      function(path) {
        return {
          controller: 'transferTableCtrl',
          controllerAs: 'trCtrl',
          restrict: ' E',
          scope: true,
          transclude: true,
          templateUrl: path + 'transfer-table/transfer-table.html',
          link: function(scope, element, attrs, ctrl, transclude) {
            var allocated = element.find('.transfer-allocated');
            var available = element.find('.transfer-available');

            transclude(scope, function(clone) {
              allocated.append(clone.filter('allocated'));
              available.append(clone.filter('available'));
            });
          }
        };
      }
    ]);

})();