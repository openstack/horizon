/*
 * Copyright 2015 IBM Corp.
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

  angular
    .module("horizon.framework.widgets.table")
    .directive('hzTableFooter', hzTableFooter);

  hzTableFooter.$inject = ['horizon.framework.widgets.basePath',
                           '$compile'];

  /**
    * @ngdoc directive
    * @name horizon.framework.widgets.table.directive:hzTableFooter
    *
    * @description
    * The `hzTableFooter` directive provides markup for a general table footer.
    * It takes an array of table items. By default, it simply prints out
    * 'Displaying x items'. However, you can provide a custom template message.
    * It will override the span tag in hz-table-footer.html.
    *
    * @restrict A
    * @scope
    *
    * @example
    * ```
    * <table>
    *   ...
    *   <tfoot hz-table-footer items="items"></tfoot>
    * </table>
    * ```
    *
    * or
    *
    * var message = "<span>{$ items.length $} items</span>";
    * ```
    * <table>
    *   ...
    *   <tfoot hz-table-footer items="items" message="{$ message $}"></tfoot>
    * </table>
    * ```
    *
    */
  function hzTableFooter(basePath, $compile) {
    var directive = {
      restrict: 'A',
      scope: {
        items: '='
      },
      templateUrl: basePath + 'table/hz-table-footer.html',
      transclude: true,
      link: link
    };

    return directive;

    function link(scope, element, attrs) {
      // use the message template if provided by the user
      if (attrs.message) {
        element.find('.display').replaceWith($compile(attrs.message)(scope));
      }
    }
  }

})();

