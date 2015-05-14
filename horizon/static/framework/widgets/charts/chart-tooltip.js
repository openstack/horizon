(function() {
  'use strict';

  angular.module('horizon.framework.widgets.charts')

    /**
     * @ngdoc directive
     * @name horizon.framework.widgets.charts.directive:chartTooltip
     * @element
     * @param {object} tooltip-data The tooltip data model and styles
     * @description
     * The `chartTooltip` directive renders a tooltip showing a colored
     * icon, label, and value.
     *
     * Data Model and Styles:
     * ```
     * var tooltipData = {
     *   enabled: true,
     *   label: 'Applied',
     *   value: 1,
     *   icon: 'fa-square',
     *   iconColor: '#333333',
     *   iconClass: 'warning',
     *   style: { left: '10px', top: '10px' }
     * };
     * ```
     *
     * @restrict E
     * @scope tooltip: '=tooltipData'
     *
     * @example
     * ```
     * <chart-tooltip tooltip-data='tooltipData'></chart-tooltip>
     * ```
     *
     */
    .directive('chartTooltip', [ 'horizon.framework.widgets.basePath', function (path) {
      return {
        restrict: 'E',
        scope: {
          tooltip: '=tooltipData'
        },
        templateUrl: path + 'charts/chart-tooltip.html'
      };
    }]);

})();