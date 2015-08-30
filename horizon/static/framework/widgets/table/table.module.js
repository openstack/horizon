/*
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 * http://www.apache.org/licenses/LICENSE-2.0
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
   * @name horizon.framework.widgets.table
   * @description
   *
   * # horizon.framework.widgets.table
   *
   * The `horizon.framework.widgets.table` provides support for user interactions and
   * checkbox selection in tables.
   *
   * Requires {@link https://github.com/lorenzofox3/Smart-Table `Smart-Table`}
   * module and jQuery (for table drawer slide animation in IE9) to be installed.
   */
  angular
    .module('horizon.framework.widgets.table', [])

    /**
     * @ngdoc parameters
     * @name horizon.framework.widgets.table.constant:expandSettings
     * @param {string} expandIconClasses Icon classes to be used for expand icon
     * @param {number} duration The slide down animation duration/speed, default: 100
     */
    .constant('horizon.framework.widgets.table.expandSettings', {
      expandIconClasses: 'fa-chevron-right fa-chevron-down',
      duration: 100
    })

    /**
     * @ngdoc parameters
     * @name horizon.framework.widgets.table.constant:filterPlaceholderText
     */
    .constant('horizon.framework.widgets.table.filterPlaceholderText',
      gettext('Filter')
    );
})();
