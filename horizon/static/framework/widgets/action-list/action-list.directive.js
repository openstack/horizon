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
   * @ngdoc directive
   * @name horizon.framework.widgets.action-list.directive:actionList
   * @element
   * @description
   * The `actionList` directive is the wrapper for the set of
   * actions to be displayed in a Bootstrap button group or
   * button dropdown.
   *
   * The following directives/elements can be declared within
   * this directive element: action, menu, and notifications.
   * Within the menu directive element, any number of `action`
   * directives elements can be declared.
   *
   * If the action list should be a button dropdown, include
   * `dropdown` as an attribute. Additionally, any attribute
   * directives can be added (i.e. warning-tooltip).
   *
   * Notifications are displayed on the bottom right of the
   * button group. Declare any number of icons to display
   * within the `notifications` element. Use `ng-show` or
   * `ng-hide` to dynamically show/hide the icon. Make sure
   * to declare <notifications> first to ensure the button
   * dropdown border radius will display as expected.
   *
   * If a button dropdown is required, declare the dropdown
   * button with the `button-type` attribute set to
   * 'single-button' or 'split-button' for a single button
   * dropdown or split button dropdown, respectively. See
   * (http://getbootstrap.com/components/#btn-dropdowns).
   * The remaining actions should be declared within the
   * `menu` directive element with the `button-type` set to
   * 'menu-item'. These will be converted to links in the
   * dropdown menu.
   *
   * See the `action` and `menu` directives below for more
   * information.
   *
   * @restrict E
   * @example
   *
   * ```
   * <action-list dropdown>
   *   <notifications>
   *     <span class="fa fa-exclamation" ng-show="disabled"></span>
   *   </notifications>
   *   <action button-type="single-button" action-classes="...">
   *     Actions
   *   </action>
   *   <menu>
   *     <action button-type="menu-item" callback="..." item="...">
   *       <span class="fa fa-pencil"></span> Edit
   *     </action>
   *     <action button-type="menu-item" callback="..." item="...">
   *       <span class="fa fa-times"></span> Delete
   *     </action>
   *   </menu>
   * </action-list>
   * ```
   */
  angular
    .module('horizon.framework.widgets.action-list')
    .directive('actionList', actionList);

  function actionList() {
    var directive = {
      link: link,
      restrict: 'E'
    };

    return directive;

    function link(scope, element) {
      element.addClass('btn-group');
    }
  }
})();
