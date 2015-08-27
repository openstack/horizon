/*
 * (c) Copyright 2015 Hewlett-Packard Development Company, L.P.
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

  angular
    .module('horizon.framework.widgets.action-list')
    .factory('horizon.framework.widgets.action-list.button-tooltip.row-warning.service', tooltip);

  tooltip.$inject = [
    '$timeout',
    'horizon.framework.widgets.basePath'
  ];

  /**
   * @ngdoc factory
   * @name horizon.framework.widgets.action-list.button-tooltip.row-warning.service
   * @description
   * Provides the default model for buttons that can not be clicked
   * because there are errors with the data in the row.
   */
  function tooltip($timeout, path) {

    var service = {
      templateUrl: path + 'action-list/warning-tooltip.html',
      data: {
        clickMessage: gettext('Click here to expand the row and view the errors.'),
        expandDetail: expandDetail
      }
    };

    return service;

    ///////////////

    function expandDetail() {
      /*eslint-disable angular/ng_controller_as_vm */
      // 'this' referred here is the this for the function not the controller
      var row = this.element.closest('tr');
      /*eslint-enable angular/ng_controller_as_vm */
      if (!row.hasClass('expanded')) {
        // Timeout needed to prevent
        // $apply already in progress error
        $timeout(function() {
          row.find('[hz-expand-detail]').click();
        }, 0, false);
      }
    }

  } // end of tooltip
})(); // end of IIFE
