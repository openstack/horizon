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
(function () {
  'use strict';

  angular
    .module('horizon.framework.widgets.table')
    .directive('hzDynamicTable', hzDynamicTable);

  hzDynamicTable.$inject = [
    'horizon.framework.widgets.basePath'
  ];

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
   * @param {function=} itemInTransitionFunction function that is called with each item in
   *   the table. If it returns true, the row is given the class "warning" which by
   *   default highlights the row with a warning color.
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
   * noItemsMessage {string} message to be displayed when the table is empty. If
   *   not provided, the default message is used.
   * columns {Array} of objects to describe each column. Each object
   *   requires: 'id', 'title', 'priority' (responsive priority when table resized)
   *   optional: 'sortDefault',
   *     'filters' (to apply to the column cells),
   *     'template' (see hz-cell directive for details),
   *     'allowed' (a promise that must resolve in order for the column to be viewed),
   *
   * This directive provides an extension point for applications to decorate additional declarative
   * column level permissions that must be fulfilled in order for the column to be viewed. For
   * example, openstack dashboard adds the following optional declarative permissions:
   *     'services' (OpenStack services that must be enabled in the current region),
   *     'settings' (horizon settings that must be enabled)
   *     'policies' (policy rules that must be allowed)
   *
   * This is accomplished by decorating the 'horizon.framework.conf.permissions' service.
   * See that service for more information.
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
   *     {id: 'e', title: 'E', allowed: allowedPromiseFunction}
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

    // TODO (tyr) In Ocata, convert to "controller as" syntax.
    // This was not done in Mitaka to avoid breaking any hz-detail-row templates that
    // assume table attributes are available directly on inherited scope.
    var directive = {
      restrict: 'E',
      scope: {
        config: '=',
        safeSrcItems: '=items',
        table: '=',
        batchActions: '=?',
        itemActions: '=?',
        filterFacets: '=?',
        resultHandler: '=?',
        itemInTransitionFunction: '=?'
      },
      controller: 'horizon.framework.widgets.table.HzDynamicTableController',
      templateUrl: basePath + 'table/hz-dynamic-table.html'
    };

    return directive;
  }
})();
