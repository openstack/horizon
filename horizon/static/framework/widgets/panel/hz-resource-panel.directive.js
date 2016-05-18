/**
 * (c) Copyright 2016 Hewlett Packard Enterprise Development Company LP
 *
 * Licensed under the Apache License, Version 2.0 (the "License"); you may
 * not use this file except in compliance with the License. You may obtain
 * a copy of the License at
 *
 *    http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
 * WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
 * License for the specific language governing permissions and limitations
 * under the License.
 */
(function() {
  'use strict';

  angular
    .module('horizon.framework.widgets.panel')
    .directive('hzResourcePanel', directive);

  directive.$inject = ['horizon.framework.widgets.basePath'];

  /**
   * @ngdoc directive
   * @name hzResourcePanel
   * @description
   * This directive takes in a resource type name, e.g. 'OS::Glance::Image'
   * as a String and produces the shell of a panel for that given resource
   * type.  This primarily includes a header and allows content to be
   * transcluded.
   *
   * @example
   ```
   <hz-resource-panel resource-type-name="OS::Nova::Server">
     <div>Here is my content!</div>
     <hz-resource-table resource-type-name="OS::Nova::Server"></hz-resource-table>
   </hz-resource-panel>
   ```
   */
  function directive(basePath) {

    var directive = {
      restrict: 'E',
      scope: {
        resourceTypeName: '@'
      },
      transclude: true,
      bindToController: true,
      templateUrl: basePath + 'panel/hz-resource-panel.html',
      controller: "horizon.framework.widgets.panel.HzResourcePanelController as ctrl"
    };

    return directive;
  }
})();
