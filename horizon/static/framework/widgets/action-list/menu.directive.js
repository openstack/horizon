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
   * @name horizon.framework.widgets.action-list.directive:menu
   * @element
   * @description
   * The `menu` directive is the wrapper for the set of
   * actions to be displayed in a dropdown menu in a
   * Bootstrap button dropdown. Actions to be displayed
   * should be declared within this directive element.
   *
   * See the `action` directive below for more information.
   *
   * @restrict E
   * @example
   *
   * ```
   * <menu>
   *   <action button-type="menu-item" callback="..." item="...">
   *     <span class="fa fa-pencil"></span> Edit
   *   </action>
   *   <action button-type="menu-item" callback="..." item="...">
   *     <span class="fa fa-times"></span> Delete
   *   </action>
   * </menu>
   * ```
   */
  angular
    .module('horizon.framework.widgets.action-list')
    .directive('menu', menu);

  menu.$inject = ['horizon.framework.widgets.basePath'];

  function menu(path) {
    var directive = {
      link: link,
      restrict: 'E',
      templateUrl: path + 'action-list/menu.html',
      transclude: true
    };

    return directive;

    function link(scope, element, attrs, ctrl, transclude) {
      var menu = element.find('ul');

      // Append menu items to menu
      transclude(scope, function (clone) {
        menu.append(clone);
      });

      // Don't include directive element since it will misalign component look
      menu.unwrap();
    }
  }
})();
