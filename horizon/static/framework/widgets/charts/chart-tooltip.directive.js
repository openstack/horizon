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
    .directive('chartTooltip', chartTooltip);

  chartTooltip.$inject = ['horizon.framework.widgets.basePath'];

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
  function chartTooltip(path) {
    var directive = {
      restrict: 'E',
      scope: {
        tooltip: '=tooltipData'
      },
      templateUrl: path + 'charts/chart-tooltip.html'
    };

    return directive;
  }
})();
