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
(function () {
  'use strict';

  angular
    .module('horizon.dashboard.project.workflow.launch-instance')
    .directive('selectFlavorTable', selectFlavorTable);

  selectFlavorTable.$inject = [
    'horizon.dashboard.project.workflow.launch-instance.basePath',
    'horizon.framework.widgets.transfer-table.helpText',
    'horizon.framework.widgets.charts.donutChartSettings',
    'horizon.framework.widgets.action-list.button-tooltip.row-warning.service'
  ];

  /**
   * @ngdoc directive
   * @name horizon.dashboard.project.workflow.launch-instance:selectFlavorTable
   * @scope true
   * @element
   * @param {boolean} isAvailableTable If true, the table is used as the
   *    "available" portion of the transfer table.
   * @param {object} items An array of flavor "facade" objects that include the data
   *    needed by each column, as well as chart data for each flavor.
   * @param {object} displayed-items Same as items, but filtered by the directives smart
   *    table to only show relevant items when search is used
   *
   * The transfer table provides a constant containing default labels when no
   * items are available. That constant is injected here.
   *
   * See flavor.html for detailed usage example.
   *
   * @example
   * '''
   * <select-flavor-table
   *    is-available-table="true"
   *    items="selectFlavorCtrl.availableFlavorFacades"
   *    displayed-items="selectFlavorCtrl.displayedAvailableFlavorFacades">
   * </select-flavor-table>
   * '''
   */
  function selectFlavorTable(basePath, transferTableHelpText, donutChartSettings, tooltipService) {

    var directive = {
      restrict: 'E',
      link: link,
      require: '^transferTable',
      scope: {
        items:              '=',
        displayedItems:     '=',
        isAvailableTable:   '=?',
        metadataDefs:       '='
      },
      templateUrl: basePath + 'flavor/select-flavor-table.html'
    };

    return directive;

    //////////

    function link(scope, element, attrs, transferTableController) {
      /*
       * Unfortunately, the transferTableController does not remove items from the data
       * when they are moved from the available to the allocated. Instead it simply
       * adds that id to its "allocatedIds" array. Tables used within the
       * transfer table directive (like this one) are required to have internal
       * knowledge about the allocatedIds and use it to determine which items
       * are currently visible.
       *
       * Also, the transferTableController item click function is different for
       * allocated items vs available items.
       *
       * Finally, the transferTableController provides default text to show when
       * the tables are empty,
       *
       * Contain all of this "parent" knowledge within "isAvailableTable"
       */
      if (scope.isAvailableTable) {
        /*
         * This table used in "available" portion of a transfer table
         */
        scope.showSearchBar = true;
        // Hide items that have been allocated
        scope.showItemFunc = function (item) {
          return !transferTableController.allocatedIds[item.id];
        };
        scope.itemClickAction = transferTableController.allocate;
        scope.noneAvailableText = transferTableHelpText.noneAvailText;
        scope.rowExpandText = transferTableHelpText.expandDetailsText;
        scope.itemButtonClasses = "fa fa-plus";

        scope.tooltipModel = tooltipService;
      } else {
        // This table used in "allocated" portion of transfer table
        scope.showSearchBar = false;
        // Always show items
        scope.showItemFunc = function () { return true; };
        scope.itemClickAction = transferTableController.deallocate;
        scope.noneAvailableText = transferTableHelpText.noneAllocText;
        scope.itemButtonClasses = "fa fa-minus";
      }

      scope.chartSettings = donutChartSettings;

      /**
       * Filtering - client-side MagicSearch
       */

      // All facets for flavor step
      scope.flavorFacets = [
        {
          label: gettext('Name'),
          name: 'name',
          singleton: true
        },
        {
          label: gettext('VCPUs'),
          name: 'vcpus',
          singleton: true
        },
        {
          label: gettext('RAM'),
          name: 'ram',
          singleton: true
        },
        {
          label: gettext('Public'),
          name: 'isPublic',
          singleton: true,
          options: [
            { label: gettext('No'), key: false },
            { label: gettext('Yes'), key: true }
          ]
        }
      ];
    } // end of link
  } // end of function

})();
