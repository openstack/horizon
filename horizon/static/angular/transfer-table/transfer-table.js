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
     * @name hz.widget.transfer-table.constant:helpContentDefaults
     * @param {string} allocTitle Title for allocation section
     * @param {string} availTitle Title for available section
     * @param {string} availHelpText Help text shown in available section
     * @param {string} allocHelpText Help text shown in allocated table
     * @param {string} noneAvailText Text shown if no available items
     * @param {string} allocHiddenText Text shown if allocated section hidden
     * @param {string} availHiddenText Text shown if available section hidden
     * @param {string} warningIcon FontAwesome icon
     */
    .constant('helpContentDefaults', {
      allocTitle: gettext('Allocated'),
      availTitle: gettext('Available'),
      availHelpText: gettext('Select one'),
      allocHelpText: gettext('Select an item from Available items below'),
      noneAvailText: gettext('No available items'),
      allocHiddenText: gettext('Expand to see allocated items'),
      availHiddenText: gettext('Expand to see available items'),
      sectionToggleText: gettext('Click to show or hide'),
      moreDetailsText: gettext('Click to see more details'),
      warningIcon: 'fa-exclamation-circle'
    })

    /**
     * @ngdoc parameters
     * @name hz.widget.transfer-table.constant:limits
     * @param {number} maxAllocation Maximum allocation allowed
     */
    .constant('limits', {
      maxAllocation: 1
    })

    /**
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
     * @name hz.widget.transfer-table.filter:filteredAvailable
     * @returns {array} List of filtered available items
     */
    .filter('filteredAvailable', function() {
      return function(items) {
        return items.filter(function (item) {
          return !item.allocated;
        });
      };
    })

    /**
     * @ngdoc filter
     * @name hz.widget.transfer-table.filter:availFoundText
     * @returns {string} Help text for filter results
     */
    .filter('availFoundText', function() {
      return function(numFound, numAvailable) {
        var transObj = { found: numFound, available: numAvailable };
        var message = gettext('Found %(found)s of %(available)s');
        return interpolate(message, transObj, true);
      };
    })

    /**
     * @ngdoc directive
     * @name hz.widget.transfer-table.directive:transferTable
     * @element
     * @param {object} trModel Table data trModel
     * @param {string} sortAlloc Enable sorting on the allocated table
     * @param {string} orderAlloc Enable manual ordering on allocated table
     * @description
     * The `transferTable` directive generates two tables and allows the
     * transfer of rows between the two tables. Headers, help text, and
     * maximum allocation are configurable. Sorting and manual ordering can
     * be enabled for the allocated table. If both are enabled, sorting is
     * disabled and manual ordering takes precedence.
     *
     * Data trModel:
     * ```
     * var headers = [
     *   { label: 'User Name', key: 'username', priority: 1 },
     *   { label: 'Email', key: 'email', priority: 2 }
     * ];
     *
     * var available = [
     *   { id: 'u1', username: 'User 1', disabled: true, warnings: { username: 'Invalid!' } },
     *   { id: 'u2', username: 'User 2' },
     *   { id: 'u3', username: 'User 3' }
     * ];
     *
     * var allocated = [];
     *
     * var tableData = {
     *   headers: headers,
     *   available: available,
     *   allocated: allocated
     * };
     * ```
     * Optional arguments for table data trModel:
     *   disabled - disables the allocate button
     *   warnings - show warning text and icon next to value in table cell
     *
     * @restrict EA
     * @scope
     *
     * @example
     * ```
     * <transfer-table tr-trModel="tableData" sort-alloc order-alloc>
     *   <div>The detail row content here</div>
     * </transfer-table>
     * ```
     */
    .directive('transferTable', [ 'basePath', 'helpContentDefaults', 'limits',
      function(path, helpContentDefaults, limits) {
        return {
          restrict: 'EA',
          scope: {
            trModel: '='
          },
          transclude: true,
          templateUrl: path + 'transfer-table/transfer-table.html',
          compile: function(tElem, tAttrs) {
            if (tAttrs.hasOwnProperty('orderAlloc') || !tAttrs.hasOwnProperty('sortAlloc')) {
              // If allocated is orderable or not sortable, remove sorting
              tElem.find('.transfer-allocated [st-sort]').removeAttr('st-sort');
            }
            if (!tAttrs.hasOwnProperty('orderAlloc')) {
              // Remove drag and drop if allocated not orderable
              tElem.find('.transfer-allocated [lr-drag-src]')
                .removeAttr('lr-drag-data lr-drag-src lr-drop-target lr-drop-success');
            }
          },
          controller: [ '$scope', function($scope) {
            var trModel = $scope.trModel;

            var model = {
              views: {
                allocated: true,
                available: true
              },
              displayedAllocated: [].concat(trModel.allocated),
              numAllocated: trModel.allocated.length
            };

            trModel.helpText = angular.extend({}, helpContentDefaults, trModel.helpText);
            trModel.limits = angular.extend({}, limits, trModel.limits);

            model.trModel = trModel;

            var unwatch = $scope.$watch("trModel.available", function() {
              model.numAvailable = trModel.available.length;
              model.displayedAvailable = [].concat(trModel.available);
            });
            $scope.$on('$destroy', unwatch);

            model.allocate = function(row) {
              if (!row.disabled) {
                if (trModel.limits.maxAllocation < 0 ||
                    model.numAllocated < trModel.limits.maxAllocation) {
                  row.allocated = true;
                  trModel.allocated.push(row);

                  model.numAllocated += 1;
                  model.numAvailable -= 1;
                } else if (trModel.limits.maxAllocation === 1) {
                  // Swap out rows if only one allocation allowed
                  model.deallocate(trModel.allocated[0]);
                  model.allocate(row);
                }
              }
            };

            model.deallocate = function(row) {
              row.allocated = false;
              trModel.allocated = trModel.allocated.filter(function(item) {
                return item.id !== row.id;
              });

              model.numAllocated -= 1;
              model.numAvailable += 1;
            };

            // Show/hide allocated or available sections
            model.toggleView = function(view) {
              var show = model.views[view];
              model.views[view] = !show;
            };

            model.updateAllocated = function(e, item, orderedItems) {
              trModel.allocated = orderedItems;
            };

            $scope.model = model;
          }]
        };
      }
    ]);

})();