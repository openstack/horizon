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

(function() {
  'use strict';

  /**
   * @ngdoc overview
   * @name horizon.framework.widgets.transfer-table
   * @description
   *
   * # horizon.framework.widgets.transfer-table
   *
   * The `horizon.framework.widgets.transfer-table` module provides support for transferring
   * rows between two tables (allocated and available).
   *
   * Requires {@link horizon.framework.widgets.table.directive:hzTable `hzTable`} module to
   * be installed.
   *
   * | Directives                                                               |
   * |--------------------------------------------------------------------------|
   * | {@link horizon.framework.widgets.transfer-table.directive:transferTable `transferTable`} |
   *
   */
  angular
    .module('horizon.framework.widgets.transfer-table', [])

    /**
     * @ngdoc parameters
     * @name horizon.framework.widgets.transfer-table.constant:helpText
     * @param {string} allocTitle Title for allocation section
     * @param {string} availTitle Title for available section
     * @param {string} availHelpText Help text shown in available section
     * @param {string} noneAllocText Text shown if no allocated items
     * @param {string} noneAvailText Text shown if no available items
     * @param {string} allocHiddenText Text shown if allocated section hidden
     * @param {string} availHiddenText Text shown if available section hidden
     * @param {string} sectionToggleText Title for section toggle chevron icon
     * @param {string} orderText Title for drag and drop re-order icon
     * @param {string} expandDetailsText Title for expand icon
     */
    .constant('horizon.framework.widgets.transfer-table.helpText', {
      allocTitle: gettext('Allocated'),
      availTitle: gettext('Available'),
      availHelpText: gettext('Select one'),
      noneAllocText: gettext('Select an item from Available items below'),
      noneAvailText: gettext('No available items'),
      allocHiddenText: gettext('Expand to see allocated items'),
      availHiddenText: gettext('Expand to see available items'),
      sectionToggleText: gettext('Click to show or hide'),
      orderText: gettext('Re-order items using drag and drop'),
      expandDetailsText: gettext('Click to see more details')
    })

    /**
     * @ngdoc parameters
     * @name horizon.framework.widgets.transfer-table.constant:limits
     * @param {number} maxAllocation Maximum allocation allowed
     */
    .constant('horizon.framework.widgets.transfer-table.limits', {
      maxAllocation: 1
    })
    .constant('horizon.framework.widgets.transfer-table.events', events());

    /**
     * @ngdoc value
     * @name horizon.framework.widgets.transfer-table.events
     * @description a list of events for transfer tables
     */
  function events() {
    return {
      AVAIL_CHANGED: 'horizon.framework.widgets.transfer-table.AVAIL_CHANGED'
    };
  }

})();
