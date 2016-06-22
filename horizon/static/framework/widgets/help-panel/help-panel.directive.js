/*
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

  angular
    .module('horizon.framework.widgets.help-panel')
    .directive('helpPanel', helpPanel);

  helpPanel.$inject = [
    'horizon.framework.widgets.basePath',
    'horizon.framework.util.uuid.service'
  ];

  /**
   * @ngdoc directive
   * @name horizon.framework.widgets.help-panel.directive:helpPanel
   * @element
   * @description
   * The `helpPanel` directive provides a help panel that can be
   * hidden or shown by clicking on the help/close icon. By default,
   * the help panel appears on the right side of the parent container.
   *
   * @restrict E
   * @example
   * ```
   * <div class="parent-container">
   *   <help-panel>My Content</help-panel>
   * </div>
   * ```
   */
  function helpPanel(path, uuid) {
    var link = function(scope) {
      scope.uuid = uuid.generate();
    };

    var directive = {
      templateUrl: path + 'help-panel/help-panel.html',
      link: link,
      transclude: true
    };

    return directive;
  }

})();
