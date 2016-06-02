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

  angular
    .module('horizon.framework.widgets.table')
    .directive('hzExpandDetail', hzExpandDetail);

  hzExpandDetail.$inject = ['horizon.framework.widgets.table.expandSettings'];

  /**
   * @ngdoc directive
   * @name horizon.framework.widgets.table.directive:hzExpandDetail
   * @element i class='fa fa-chevron-right'
   * @param {number} duration The duration for drawer slide animation
   * @description
   * The `hzExpandDetail` directive toggles the detailed drawer of the row.
   * The animation is implemented using jQuery's slideDown() and slideUp().
   * Assign this as an attribute to an icon that should trigger the toggle,
   * passing in the two class names of the icon. If no class names are
   * specified, the default 'fa-chevron-right fa-chevron-down' is used. A
   * duration for the slide animation can be specified as well (default: 400).
   * The detail drawer row and cell also needs to be implemented and include
   * the classes 'detail-row' and 'detail', respectively. On expansion,
   * the directive will broadcast the optionally supplied item from the template.
   *
   * @restrict A
   * @scope icons: '@hzExpandDetail', duration: '@', item: '=?'
   * @example
   *
   * ```
   * <tr>
   *  <td>
   *    <i class='fa fa-chevron-right'
   *       hz-expand-detail='fa-chevron-right fa-chevron-down'
   *       duration='200'
   *       item="someObject"></i>
   *  </td>
   * </tr>
   * <tr class='detail-row'>
   *  <td class='detail'></td>
   * </tr>
   * ```
   *
   */
  function hzExpandDetail(settings) {
    var directive = {
      restrict: 'A',
      require: '?^hzTable',
      scope: {
        icons: '@hzExpandDetail',
        duration: '@',
        item: '=?'
      },
      link: link
    };
    return directive;

    ////////////////////

    function link(scope, element, attrs, hzTableCtrl) {
      element.on('click', onClick);

      function onClick() {
        var iconClasses = scope.icons || settings.expandIconClasses;
        element.toggleClass(iconClasses);

        var summaryRow = element.closest('tr');
        var detailCell = summaryRow.next('tr').find('.detail');
        var duration = scope.duration ? parseInt(scope.duration, 10) : settings.duration;

        if (summaryRow.hasClass('expanded')) {
          var options = {
            duration: duration,
            complete: function() {
              // Hide the row after the slide animation finishes
              summaryRow.toggleClass('expanded');
            }
          };

          detailCell.find('.detail-expanded').slideUp(options);
        } else {
          summaryRow.toggleClass('expanded');

          if (detailCell.find('.detail-expanded').length === 0) {
            // Slide down animation doesn't work on table cells
            // so a <div> wrapper needs to be added
            detailCell.wrapInner('<div class="detail-expanded"></div>');
          }

          if (scope.item && hzTableCtrl) {
            hzTableCtrl.broadcastExpansion(scope.item);
          }

          detailCell.find('.detail-expanded').slideDown(duration);
        }
      }
    }
  }
})();
