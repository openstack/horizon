(function() {
  'use strict';

  /**
   * @ngdoc overview
   * @name hz.widget.charts
   * @description
   *
   * # hz.widget.charts
   *
   * The `hz.widget.charts` module provides directives for simple charts
   * used in Horizon, such as the pie and donut chart. Charts are
   * implemented using D3.
   *
   * Requires {@link http://d3js.org `D3`} to be installed.
   *
   * | Constants                                                       |
   * |-----------------------------------------------------------------|
   * | {@link hz.widget.charts.constant:chartSettings `chartSettings`} |
   *
   * | Directives                                                      |
   * |-----------------------------------------------------------------|
   * | {@link hz.widget.charts.directive:pieChart `pieChart`}          |
   *
   */
  angular.module('hz.widget.charts', [])

    /**
     * @ngdoc parameters
     * @name hz.widget.charts.constant:chartsettings
     * @param {number} innerRadius Pie chart inner radius in pixels, default: 0
     * @param {number} outerRadius Pie chart outer radius in pixels, default: 35
     * @param {boolean} showTitle Show title, default: true
     * @param {boolean} showLabel Show label, default: true
     * @param {boolean} showLegend Show legend default: true
     * @param {string} tooltipIcon Tooltip key icon, default: 'fa-square'
     *
     */
    .constant('chartSettings', {
      innerRadius: 0,
      outerRadius: 35,
      showTitle: true,
      showLabel: true,
      showLegend: true,
      tooltipIcon: 'fa-square'
    })

    /**
     * @ngdoc filter
     * @name hz.widget.charts.filter:showKeyFilter
     * @function Filter based on 'hideKey' value of each slice
     * @returns {function} A filtered list of keys to show in legend
     *
     */
    .filter('showKeyFilter', function() {
      return function(items) {
        return items.filter(function (item) {
          return !item.hideKey;
        });
      };
    });

})();