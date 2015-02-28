(function() {
  'use strict';

  angular.module('hz.widget.charts')

    /**
     * @ngdoc directive
     * @name hz.widget.charts.directive:pieChart
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
     *    data: [
     *      { label: 'Current', value: 1, color: '#1f83c6' },
     *      { label: 'Added', value: 1, color: '#81c1e7' },
     *      { label: 'Remaining', value: 6, colorClass: 'remaining', hideKey: true }
     *    ]
     * };
     *
     * title - the chart title
     * label - the text to show in center of chart
     * data - the data used to render chart
     *
     * var chartSettings = {
     *   innerRadius: 35,
     *   outerRadius: 50,
     *   showLabel: false
     * };
     * ```
     *
     * @restrict E
     * @scope true
     *
     * @example
     * ```
     * Pie Chart:
     * <pie-chart chart-data='chartData'></pie-chart>
     *
     * Donut Chart:
     * <pie-chart chart-data='chartData'
     *            chart-settings='chartSettings'></pie-chart>
     * ```
     *
     */
    .directive('pieChart', [ 'basePath', 'chartSettings', function (path, chartSettings) {
      return {
        restrict: 'E',
        scope: {
          chartData: '=',
          chartSettings: '='
        },
        replace: true,
        templateUrl: path + 'charts/pie-chart.html',
        link: function (scope, element, attrs) {
          var settings = angular.extend({}, chartSettings, scope.chartSettings);
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

          var tooltip = d3Elt.select('chart-tooltip');

          var unwatch = scope.$watch('chartData', updateChart);
          scope.$on('$destroy', unwatch);

          scope.model = model;

          function updateChart() {
            scope.model.total = d3.sum(scope.chartData.data, function(d) { return d.value; });
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