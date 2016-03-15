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
   * @name horizon.framework.widgets.action-list.directive:action
   * @element
   * @description
   * The `action` directive represents the actions to be
   * displayed in a Bootstrap button group or button
   * dropdown. Any content within this directive element
   * will be appended to the button or link element.
   *
   * There are 4 button types available to an
   * action (`button-type` attribute):
   *
   * Default: <button>
   * Single: <button> with caret icon, use 'single-button'
   * Split: <button> with caret button, use 'split-button'
   * Menu item: <a> wrapped by <li>, use 'menu-item'
   *
   * Attributes:
   *
   * actionClasses: classes added to button or link
   * callback: function called when button clicked or link needed for rendering
   * disabled: disable/enable button dynamically
   * item: object passed to callback function
   *
   * @restrict E
   * @scope
   * @example
   *
   * ```
   * <action button-type="single-button" action-classes="myClasses">
   *   Actions
   * </action>
   *
   * <action button-type="split-button" callback="edit" disabled="editDisabled">
   *   <span class="fa fa-pencil"></span> Edit
   * </action>
   *
   * <action button-type="menu-item" callback="delete" item="row">
   *   Delete
   * </action>
   *
   * <action button-type="link" callback="generateUrl" item="row">
   *   Download
   * </action>
   * ```
   */
  angular
    .module('horizon.framework.widgets.action-list')
    .directive('action', action);

  action.$inject = ['horizon.framework.widgets.basePath'];

  function action(path) {
    var directive = {
      link: link,
      restrict: 'E',
      scope: {
        actionClasses: '=?',
        callback: '=?',
        disabled: '=?',
        item: '=?'
      },
      templateUrl: templateUrl,
      transclude: true
    };

    return directive;

    function link(scope, element) {
      // Don't include directive element since it will misalign component look
      element.children().first().unwrap();
    }

    function templateUrl(element, attrs) {
      // Load the template for the action type
      var buttonType = attrs.buttonType || 'action';
      return path + 'action-list/' + buttonType + '.html';
    }
  }
})();
