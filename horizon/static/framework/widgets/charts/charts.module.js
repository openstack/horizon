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

  /**
   * @ngdoc overview
   * @name horizon.framework.widgets.charts
   * @description
   *
   * # horizon.framework.widgets.charts
   *
   * The `horizon.framework.widgets.charts` module provides directives for simple charts
   * used in Horizon, such as the pie and donut chart. Charts are
   * implemented using D3.
   *
   * Requires {@link http://d3js.org `D3`} to be installed.
   *
   * | Constants                                                                 |
   * |---------------------------------------------------------------------------|
   * | {@link horizon.framework.widgets.charts.constant:donutChartSettings `donutChartSettings`} |
   * | {@link horizon.framework.widgets.charts.constant:quotaChartDefaults `quotaChartDefaults`} |
   *
   * | Directives                                                                |
   * |---------------------------------------------------------------------------|
   * | {@link horizon.framework.widgets.charts.directive:pieChart `pieChart`}                    |
   *
   */
  angular
    .module('horizon.framework.widgets.charts', [])

  /**
   * @ngdoc parameters
   * @name horizon.framework.widgets.charts.constant:donutChartSettings
   * @param {number} innerRadius Pie chart inner radius in pixels, default: 24
   * @param {number} outerRadius Pie chart outer radius in pixels, default: 30
   * @param {object} label with properties font-size and fill (optional)
   * @param {string} titleClass CSS class to override title,
   *  default: pie-chart-title-medium
   *  alternative: pie-chart-title-large
   * @param {boolean} showTitle Show title, default: true
   * @param {boolean} showLabel Show label, default: true
   * @param {boolean} showLegend Show legend default: true
   * @param {string} tooltipIcon Tooltip key icon, default: 'fa-square'
   *
   */
  .constant('horizon.framework.widgets.charts.donutChartSettings', {
    innerRadius: 24,
    outerRadius: 36,
    titleClass: 'pie-chart-title-medium',
    showTitle: true,
    showLabel: true,
    showLegend: true,
    tooltipIcon: 'fa-square'
  })

  /**
   * @ngdoc parameters
   * @name horizon.framework.widgets.charts.constant:pieChartSettings
   * @param {number} innerRadius Pie chart inner radius in pixels, default: 0
   * @param {number} outerRadius Pie chart outer radius in pixels, default: 30
   * @param {object} label with properties font-size and fill (optional)
   * @param {string} titleClass CSS class to override title,
   *  default: pie-chart-title-medium
   *  alternative: pie-chart-title-large
   * @param {boolean} showTitle Show title, default: true
   * @param {boolean} showLabel Show label, default: true
   * @param {boolean} showLegend Show legend default: true
   * @param {string} tooltipIcon Tooltip key icon, default: 'fa-square'
   *
   */
  .constant('horizon.framework.widgets.charts.pieChartSettings', {
    innerRadius: 0,
    outerRadius: 30,
    titleClass: 'pie-chart-title-medium',
    showTitle: true,
    showLabel: true,
    showLegend: true,
    tooltipIcon: 'fa-square'
  })

  /**
   * @ngdoc parameters
   * @name horizon.framework.widgets.charts.constant:quotaChartDefaults
   * @param {string} usageLabel label text for Usage, default: 'Current Usage'
   * @param {string} usageColorClass css class for Usage , default: 'usage'
   * @param {string} addedLabel label text for Added, default: 'Added'
   * @param {string} addedColorClass CSS class for Added , default: 'added'
   * @param {string} remainingLabel label text for Remaining, default: 'Remaining'
   * @param {string} remainingColorClass CSS class for Remaining , default: 'remaining'
   *
   */
  .constant('horizon.framework.widgets.charts.quotaChartDefaults', {
    usageLabel: gettext('Current Usage'),
    usageColorClass: 'usage',
    addedLabel: gettext('Added'),
    addedColorClass: 'added',
    remainingLabel: gettext('Remaining'),
    remainingColorClass: 'remaining'
  })
  .filter('showKeyFilter', showKeyFilter);

  /**
   * @ngdoc filter
   * @name horizon.framework.widgets.charts.filter:showKeyFilter
   * @function Filter based on 'hideKey' value of each slice
   * @returns {function} A filtered list of keys to show in legend
   *
   */
  function showKeyFilter() {
    return function (items) {
      return items.filter(function (item) {
        return !item.hideKey;
      });
    };
  }
})();
