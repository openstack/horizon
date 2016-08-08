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

  hzCell.$inject = ['$compile'];

  /**
   * @ngdoc directive
   * @name horizon.framework.widgets.table.directive:hzCell
   * @param table {Object} - The table/controller context
   * @param column {Object} - The column definition object, described below
   * @param item {Object} - The object containing the property from column.id
   * @description
   * The `hzCell` directive allows you to customize your cell content.
   * When specifying your table configuration object, you may pass in a
   * template per each column.
   *
   * See the documentation on hz-field for details on how to specify formatting
   * based on the column configuration.
   *
   * You should define a template when you want to format data or show more
   * complex content (e.g conditionally show different icons or a link).
   * You should reference the cell's 'item' attribute in the template if
   * you need access to the cell's data. See example below.
   *
   * It should ideally be used within the context of the `hz-dynamic-table` directive.
   * 'table' can be referenced in a template if you want to pass in an outside scope.
   *
   * If the column has a itemInTransitionFunction property, that function will be
   * called with the row's item. If the function returns true, a progress bar will
   * be included in the cell.
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
   *       filters: [someFilterFunction, 'uppercase']},
   *     {id: 'e', title: 'Header E', priority: 1,
   *       values: {
   *         'a': 'apple',
   *         'j': 'jacks'
   *       }
   *     },
   *     {id: 'f', title: 'Status', itemInTransitionFunction: myInTransitionFunc},
   *   ]
   * };
   *
   * ```
   * <tbody ng-controller="TableCtrl as table">
   *   <tr ng-repeat="item in items track by $index">
   *     <td ng-repeat="column in config.columns"
   *       class="{$ column.classes $}">
   *         <hz-cell table="table" column="column" item="item"></hz-cell>
   *     </td>
   *   </tr>
   * </tbody>
   * ```
   *
   */
  function hzCell($compile) {

    var directive = {
      restrict: 'E',
      scope: {
        table: '=',
        column: '=',
        item: '='
      },
      link: link
    };
    return directive;

    ///////////////////

    function link(scope, element) {
      var column = scope.column;
      var html;
      var progressBarHtml = '';
      if (column && column.template) {
        // if template provided, render, and place into cell
        html = $compile(column.template)(scope);
      } else {
        // NOTE: 'table' is not passed to hz-field as hz-field is intentionally
        // not cognizant of a 'table' context as hz-cell is.
        if (column.itemInTransitionFunction && column.itemInTransitionFunction(scope.item)) {
          // NOTE(woodnt): It'd be nice to split this out into a template file,
          //               but since we're inside a link function, that's complicated.
          progressBarHtml = '<div class="progress-text horizon-loading-bar">' +
                              '<div class="progress progress-striped active">' +
                                '<div class="progress-bar"></div>' +
                              '</div>' +
                            '</div>';
        }
        html = $compile(progressBarHtml +
                        '<hz-field config="column" item="item"></hz-field>')(scope);
      }
      element.append(html);
    }
  }
})();
