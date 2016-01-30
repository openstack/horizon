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
    .directive('hzDynamicTable', hzDynamicTable);

  hzDynamicTable.$inject = ['horizon.framework.widgets.basePath'];

  /**
   * @ngdoc directive
   * @name horizon.framework.widgets.table.directive:hzDynamicTable
   * @restrict E
   *
   * @param {object} config column definition used to generate the table (required)
   * @param {object} items displayed row collection (required)
   * @param {object} safeItems safe row collection (required)
   * @param {object=} table any additional information that are
   *   passed down to child widgets (e.g hz-cell) (optional)
   * @param {object=} batchActions batch actions for the table (optional)
   * @param {object=} itemActions item actions for each item/row (optional)
   * @param {object=} filterFacets Facets allowed for searching, if not provided,
   *   default to simple text search (optional)
   * @param {function=} resultHandler function that is called with return value
   *   from a clicked actions perform function passed into `actions` directive (optional)
   *
   * @description
   * The `hzDynamicTable` directive generates all the HTML content for a table.
   * You will need to pass in three attributes: `config`, `items`, and `safe-src-items`.
   *
   * This directive is built off the Smart-table module, so `items` and `safe-src-items`
   * are passed into `st-table` and `st-safe-src` attribute, respectively.
   * Note: `st-safe-src' is used for async data, to keep track of modifications to the
   *       collection. Also, 'name' is the key used to retrieve cell data from base
   *       'displayedCollection'
   *
   * @example
   *
   * var config = {
   *   selectAll: true,
   *   expand: true,
   *   trackId: 'id',
   *   columns: [
   *     {id: 'a', title: 'A', priority: 1},
   *     {id: 'b', title: 'B', priority: 2},
   *     {id: 'c', title: 'C', priority: 1, sortDefault: true},
   *     {id: 'd', title: 'D', priority: 2, filters: [myFilter, 'yesno']}
   *   ]
   * };
   * ```
   * <hz-dynamic-table
   *   config='config'
   *   items='items'
   *   safe-src-items="safeSrcItems">
   * </hz-dynamic-table>
   *
   * <hz-dynamic-table
   *   config='config'
   *   items='items'
   *   safe-src-items="safeSrcItems"
   *   table="table"
   *   batchActions="batchActions"
   *   itemActions="itemActions"
   *   filterFacets="filterFacets"
   *   resultHandler="resultHandler">
   * </hz-dynamic-table>
   * ```
   *
   */
  function hzDynamicTable(basePath) {

    var directive = {
      restrict: 'E',
      scope: {
        config: '=',
        items: '=',
        safeSrcItems: '=',
        table: '=',
        batchActions: '=?',
        itemActions: '=?',
        filterFacets: '=?',
        resultHandler: '=?'
      },
      templateUrl: basePath + 'table/hz-dynamic-table.html'
    };

    return directive;
  }
})();
