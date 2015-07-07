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

  /**
   * @ngdoc overview
   * @name horizon.framework.widgets.action-list
   * @description
   *
   * # horizon.framework.widgets.action-list
   *
   * The `actionList` directive supports displaying a set of buttons
   * in a Bootstrap button group or button dropdown (single or split).
   *
   * | Directives                                                      |
   * |-----------------------------------------------------------------|
   * | {@link horizon.framework.widgets.action-list.directive:actionList `actionList`} |
   * | {@link horizon.framework.widgets.menu.directive:menu `menu`}                    |
   * | {@link horizon.framework.widgets.action.directive:action `action`}              |
   *
   */
  angular
    .module('horizon.framework.widgets.action-list', [])

  /**
   * @ngdoc parameters
   * @name horizon.framework.widgets.action-list.constant:tooltipConfig
   * @param {string} defaultTemplate Default warning tooltip template
   * @param {string} defaultMessage Default warning tooltip message
   */
  .constant('horizon.framework.widgets.action-list.tooltipConfig', {
    defaultTemplate: '<div>{$ ::message $}</div>',
    defaultMessage: {
      /*eslint-disable max-len */
      message: gettext('The action cannot be performed. The contents of this row have errors or are missing information.')
      /*eslint-enable max-len */
    }
  });
})();
