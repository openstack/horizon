(function() {
  'use strict';

  angular.module('horizon.framework.widgets.charts')

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
    .directive('pieChart', [ 'horizon.framework.widgets.basePath', 'horizon.framework.widgets.charts.donutChartSettings', function (path, donutChartSettings) {
      return {
        restrict: 'E',
        scope: {
          chartData: '=',
          chartSettings: '='
        },
        replace: true,
        templateUrl: path + 'charts/pie-chart.html',
        link: function (scope, element) {
          var settings = {};
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

          var d3Elt = d3.select(element[0]);

          var arc = d3.svg.arc()
                          .outerRadius(settings.outerRadius)
                          .innerRadius(settings.innerRadius);

          var pie = d3.layout.pie()
                              .sort(null)
                              .value(function(d) { return d.value; });

          var unwatch = scope.$watch('chartData', updateChart);
          scope.$on('$destroy', unwatch);

          scope.model = model;

          function updateChart() {
            // set labels depending on whether this is a max or total chart
            if (angular.isDefined(scope.chartData.maxLimit)) {
              scope.model.total = scope.chartData.maxLimit;
              scope.model.totalLabel = gettext('Max');
            } else {
              scope.model.total = d3.sum(scope.chartData.data, function(d) { return d.value; });
              scope.model.totalLabel = gettext('Total');
            }
            scope.model.tooltipData.enabled = false;

            // Generate or update slices
            var chart = d3Elt.select('.slices')
                            .selectAll('path.slice')
                            .data(pie(scope.chartData.data));

            chart.enter().append('path')
                          .attr('class', 'slice')
                          .attr('d', arc);

            // Set the color or CSS class for the fill
            chart.each(function(d) {
              var slice = d3.select(this);
              if (d.data.color) {
                slice.style('fill', d.data.color);
              } else if (d.data.colorClass) {
                slice.classed(d.data.colorClass, true);
              }
            });

            chart.on('mouseenter', function(d) { showTooltip(d, this); })
              .on('mouseleave', clearTooltip);

            // Animate the slice rendering
            chart.transition()
                  .duration(500)
                  .attrTween('d', function animate(d) {
                    this.lastAngle = this.lastAngle || { startAngle: 0, endAngle: 0 };
                    var interpolate = d3.interpolate(this.lastAngle, d);
                    this.lastAngle = interpolate(0);

                    return function(t) {
                      return arc(interpolate(t));
                    };
                  });

            chart.exit().remove();
          }

          function showTooltip(d, elt) {
            scope.$apply(function() {
              var eltHeight = element[0].getBoundingClientRect().height;
              var titleHeight = element[0].querySelector('div.pie-chart-title')
                                            .getBoundingClientRect()
                                            .height;

              var point = d3.mouse(elt);
              var x = point[0] + scope.model.settings.outerRadius;
              var y = eltHeight - point[1] - scope.model.settings.outerRadius - titleHeight;

              scope.model.tooltipData.label = d.data.label;
              scope.model.tooltipData.value = d.data.value;
              scope.model.tooltipData.enabled = true;
              scope.model.tooltipData.iconColor = d.data.color;
              scope.model.tooltipData.iconClass = d.data.colorClass;
              scope.model.tooltipData.style.left = x + 'px';
              scope.model.tooltipData.style.bottom = y + 'px';
            });
          }

          function clearTooltip() {
            scope.$apply(function() {
              scope.model.tooltipData.enabled = false;
            });
          }
        }
      };
    }]);

})();
