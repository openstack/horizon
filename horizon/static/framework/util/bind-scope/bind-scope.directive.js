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
   * @name horizon.framework.util.bind-scope.directive:bindScope
   * @element ng-repeat
   * @description
   * The `bindScope` directive injects the scope where it is
   * instantiated into the transclusion function so that the
   * transcluded content is rendered correctly. The content
   * is then append to the element where 'bind-scope-target'
   * is defined.
   *
   * @restrict A
   *
   * @example
   * ```
   * <tr ng-repeat bind-scope>
   *   <td></td>
   *   <td class="detail" bind-scope-target>
   *   </td>
   * </tr>
   * ```
   */
  angular
    .module('horizon.framework.util.bind-scope')
    .directive('bindScope', bindScope);

  function bindScope() {
    var directive = {
      restrict: 'A',
      link: link
    };

    return directive;

    //////////

    function link(scope, element, attrs, ctrl, transclude) {
      if (transclude) {
        transclude(scope, function (clone) {
          var detailElt = element.find('[bind-scope-target]');
          if (detailElt.length) {
            detailElt.append(clone);
          }
        });
      }
    }
  }
})();
