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
   * @param {object} items original collection, passed into 'st-safe-src' attribute (required)
   * @param {object=} table is the name of a controller that should be passed
   *   down to child widgets (e.g hz-cell) for additional attribute access (optional)
   * @param {object=} batchActions batch action-list actions for the table (optional)
   * @param {object=} itemActions item action-list actions for each item/row (optional)
   * @param {object=} filterFacets Facets used by hz-magic-search-context allowed for
   *   searching. Filter will not be shown if this is not supplied (optional)
   * @param {function=} resultHandler function that is called with return value
   *   from a clicked actions perform function passed into `actions` directive (optional)
   *
   * @description
   * The `hzDynamicTable` directive generates all the HTML content for a table.
   * You will need to pass in two attributes: `config` and `items`.
   * This directive is built off the Smart-table module, so `items`
   * is passed into `st-table` attribute.
   *
   * You can pass the following into `config` object:
   * selectAll {boolean} set to true if you want to enable select all checkbox
   * expand {boolean} set to true if you want to inline details
   * trackId {string} passed into ngRepeat's track by to identify objects
   * columns {Array} of objects to describe each column. Each object
   *   requires: 'id', 'title', 'priority' (responsive priority when table resized)
   *   optional: 'sortDefault', 'filters' (to apply to the column cells),
   *     'template' (see hz-cell directive for details)
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
   *   items='items'>
   * </hz-dynamic-table>
   *
   * <hz-dynamic-table
   *   config='config'
   *   items="items"
   *   table="table"
   *   batch-actions="batchActions"
   *   item-actions="itemActions"
   *   filter-facets="filterFacets"
   *   result-handler="resultHandler">
   * </hz-dynamic-table>
   * ```
   *
   */
  function hzDynamicTable(basePath) {

    // <r1chardj0n3s>: there are some configuration items which are on the directive,
    // and some on the "config" attribute of the directive. Those latter configuration
    // items will be effectively "static" for the lifespan of the directive whereas
    // angular will watch directive attributes for changes. This should be revisited
    // at some point to make sure the split we've actually got here makes sense.
    var directive = {
      restrict: 'E',
      scope: {
        config: '=',
        safeSrcItems: '=items',
        table: '=',
        batchActions: '=?',
        itemActions: '=?',
        filterFacets: '=?',
        resultHandler: '=?'
      },
      templateUrl: basePath + 'table/hz-dynamic-table.html',
      link: link
    };

    return directive;

    function link(scope) {
      scope.items = [];

      // if selectAll and expand are not set in the config, default set to true

      if (angular.isUndefined(scope.config.selectAll)) {
        scope.config.selectAll = true;
      }
      if (angular.isUndefined(scope.config.expand)) {
        scope.config.expand = true;
      }
    }
  }
})();
