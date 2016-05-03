/**
 * Copyright 2016 IBM Corp.
 *
 * Licensed under the Apache License, Version 2.0 (the "License"); you may
 * not use this file except in compliance with the License. You may obtain
 * a copy of the License at
 *
 *    http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
 * WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
 * License for the specific language governing permissions and limitations
 * under the License.
 */
(function() {
  'use strict';

  angular
    .module('horizon.framework.widgets.table')
    .directive('hzCell', hzCell);

  hzCell.$inject = ['$compile', '$filter'];

  /**
   * @ngdoc directive
   * @name horizon.framework.widgets.table.directive:hzCell
   * @description
   * The `hzCell` directive allows you to customize your cell content.
   * When specifying your table configuration object, you may pass in a
   * template per each column.
   *
   * You should define a template when you want to format data or show more
   * complex content (e.g conditionally show different icons or a link).
   * You should reference the cell's 'item' attribute in the template if
   * you need access to the cell's data. The attributes 'column' and 'item'
   * should be defined outside of this directive. See example below.
   *
   * It should ideally be used within the context of the `hz-dynamic-table` directive.
   * The params passed into `hz-dynamic-table` can be used in the custom template,
   * including the 'table' scope.
   *
   * @restrict E
   *
   * @scope
   * @example
   *
   * var config = {
   *   selectAll: true,
   *   expand: true,
   *   columns: [
   *     {id: 'a', title: 'Header A', priority: 1},
   *     {id: 'b', title: 'Header B', priority: 2},
   *     {id: 'c', title: 'Header C', priority: 1, sortDefault: true},
   *     {id: 'd', title: 'Header D', priority: 2,
   *       template: '<span class="fa fa-bolt">{$ item.id $}</span>',
   *       filters: [someFilterFunction, 'uppercase']}
   *   ]
   * };
   *
   * ```
   * <tbody>
   *   <tr ng-repeat="item in items track by $index">
   *     <td ng-repeat="column in config.columns"
   *       class="{$ column.classes $}">
   *         <hz-cell></hz-cell>
   *     </td>
   *   </tr>
   * </tbody>
   * ```
   *
   */
  function hzCell($compile, $filter) {

    var directive = {
      restrict: 'E',
      scope: false,
      link: link
    };
    return directive;

    ///////////////////

    function link(scope, element) {
      var column = scope.column;
      var item = scope.item;
      var html;
      // if template provided, render, and place into cell
      if (column && column.template) {
        html = $compile(column.template)(scope);
      } else {
        // apply filters to cell data if applicable
        html = item[column.id];
        if (column && column.filters) {
          for (var i = 0; i < column.filters.length; i++) {
            var filter = column.filters[i];
            // call horizon framework filter function if provided
            if (angular.isFunction(filter)) {
              html = filter(item[column.id]);
            // call angular filters
            } else {
              html = $filter(filter)(item[column.id]);
            }
          }
        }
      }
      element.append(html);
    }
  }
})();
