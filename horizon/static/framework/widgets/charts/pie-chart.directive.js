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
    .module('horizon.framework.widgets.charts')
    .directive('pieChart', pieChart);

  pieChart.$inject = [
    'horizon.framework.widgets.basePath',
    'horizon.framework.widgets.charts.donutChartSettings'
  ];

  /*eslint-disable max-len */
  /**
   * @ngdoc directive
   * @name horizon.framework.widgets.charts.directive:pieChart
   * @element
   * @param {object} chart-data The chart data model
   * @param {string} chart-settings The custom chart settings (JSON), optional
   * @description
   * The `pieChart` directive renders a pie or donut chart using D3. The title
   * and legend is shown by default. Each slice is represented by a label, value,
   * and color (hex value or CSS class). See below for the data model.
   *
   * Data Model:
   * ```
   * var chartData = {
   *    title: 'Total Instances',
   *    label: '25%',
   *    maxLimit: 10,
   *    overMax: false,
   *    data: [
   *      { label: quotaChartDefaults.usageLabel, value: 1, colorClass: quotaChartDefaults.usageColorClass},
   *      { label: quotaChartDefaults.addedLabel, value: 1, colorClass: quotaChartDefaults.addedColorClass },
   *      { label: quotaChartDefaults.remainingLabel, value: 1, colorClass: quotaChartDefaults.remainingColorClass }
   *    ]
   * };
   *
   * title - the chart title
   * label - the text to show in center of chart
   * maxLimit - the max limit for current item (optional)
   *  - if a maxLimit is specified, (# Max) will get added to the chart title
   *  - otherwise (# Total) will be added to the chart title
   * overMax - used to notify view when max is surpassed so that we can
   *  dynamically alter UI to warn the user (optional)
   * data - the data used to render chart
   *
   * Donut chart settings (donutChartSettings) and pie chart settings (pieChartSettings)
   * are conveniently defined as angular constants in order to encourage consistency.
   * To leverage the constant values, you will need to specify them as dependencies
   * in your controller or directive. You can also create a custom styled chart
   * by defining a chartSettings object in your controller and passing it in as
   * the chart-settings attribute value.
   *
   * var chartSettings = {
   *    innerRadius: 24,
   *    outerRadius: 30,
   *    titleClass: 'pie-chart-title-medium',
   *    showTitle: true,
   *    showLabel: true,
   *    showLegend: true,
   *    tooltipIcon: 'fa-square'
   * };
   * ```
   *
   * @restrict E
   * @scope true
   *
   * @example
   * ```
   * Pie Chart using predefined constant:
   * <pie-chart chart-data='chartData'
   *            chart-settings='pieChartSettings'></pie-chart>
   *
   * Donut Chart using predefined constant:
   * <pie-chart chart-data='chartData'
   *            chart-settings='donutChartSettings'></pie-chart>
   *
   * Custom Chart using custom settings:
   * <pie-chart chart-data='chartData'
   *            chart-settings='chartSettings'></pie-chart>
   * ```
   *
   */
  /*eslint-enable max-len */
  function pieChart(path, donutChartSettings) {
    var directive = {
      link: link,
      replace: true,
      restrict: 'E',
      scope: {
        chartData: '=',
        chartSettings: '='
      },
      templateUrl: path + 'charts/pie-chart.html'
    };

    return directive;

    function link(scope, element) {
      function updateChartVisibility() {
        var showChart = scope.chartData.maxLimit !== Infinity;
        scope.chartData.showChart = showChart;
        scope.chartData.chartless = showChart ? '' : 'chartless';
        return showChart;
      }

      var settings = {};
      var showChart = updateChartVisibility();

      // if chartSettings is defined via the attribute value, use it
      if (angular.isObject(scope.chartSettings)) {
        settings = scope.chartSettings;
      } else {
        // else default to a donut chart
        settings = angular.extend({}, donutChartSettings, scope.chartSettings);
      }
      settings.diameter = settings.outerRadius * 2;

      var model = {
        settings: settings,
        tooltipData: {
          enabled: false,
          icon: settings.tooltipIcon,
          style: angular.extend({}, settings.tooltip)
        }
      };

      if (showChart) {
        var d3Elt = d3.select(element[0]);

        var arc = d3.svg.arc()
          .outerRadius(settings.outerRadius)
          .innerRadius(settings.innerRadius);

        var pie = d3.layout.pie()
          .sort(null)
          .value(function (d) { return d.value; });
      }

      var unwatch = scope.$watch('chartData', updateChart);
      scope.$on('$destroy', unwatch);

      scope.model = model;

      function updateChart() {
        var showChart = updateChartVisibility();
        angular.forEach(scope.chartData.data, function(item) {
          if (item.value === Infinity) {
            item.hideKey = true;
          }
        });

        // set labels depending on whether this is a max or total chart
        if (!showChart) {
          scope.model.total = null;
          scope.model.totalLabel = gettext('no quota');
        } else if (angular.isDefined(scope.chartData.maxLimit)) {
          scope.model.total = scope.chartData.maxLimit;
          scope.model.totalLabel = gettext('Max');
        } else {
          scope.model.total = d3.sum(scope.chartData.data, function (d) { return d.value; });
          scope.model.totalLabel = gettext('Total');
        }
        scope.model.tooltipData.enabled = false;

        // Generate or update slices
        if (showChart) {
          var chart = d3Elt.select('.slices')
            .selectAll('path.slice')
            .data(pie(scope.chartData.data));

          chart.enter().append('path')
            .attr('class', 'slice')
            .attr('d', arc);

          // Set the color or CSS class for the fill
          chart.each(function (d) {
            var slice = d3.select(this);
            if (d.data.color) {
              slice.style('fill', d.data.color);
            } else if (d.data.colorClass) {
              slice.classed(d.data.colorClass, true);
            }
          });

          chart.on('mouseenter', function (d) { showTooltip(d, this); })
            .on('mouseleave', clearTooltip);

          // Animate the slice rendering
          chart.transition()
            .duration(500)
            .attrTween('d', function animate(d) {
              this.lastAngle = this.lastAngle || { startAngle: 0, endAngle: 0 };
              var interpolate = d3.interpolate(this.lastAngle, d);
              this.lastAngle = interpolate(0);

              return function (t) {
                return arc(interpolate(t));
              };
            });

          chart.exit().remove();
        }
      }

      function showTooltip(d, elt) {
        scope.$apply(function () {
          var chartElt = element[0];
          var eltHeight = chartElt.getBoundingClientRect().height;
          var titleHeight = chartElt.querySelector('div.pie-chart-title')
                                    .getBoundingClientRect()
                                    .height;

          var point = d3.mouse(elt);
          var outerRadius = scope.model.settings.outerRadius;
          var x = point[0] + outerRadius;
          var y = eltHeight - point[1] - outerRadius - titleHeight;

          var newTooltipData = {
            label: d.data.label,
            value: d.data.value,
            enabled: true,
            iconColor: d.data.color,
            iconClass: d.data.colorClass,
            style: {
              left: x + 'px',
              bottom: y + 'px'
            }
          };
          angular.extend(scope.model.tooltipData, newTooltipData);
        });
      }

      function clearTooltip() {
        scope.$apply(function () {
          scope.model.tooltipData.enabled = false;
        });
      }
    }
  }
})();
