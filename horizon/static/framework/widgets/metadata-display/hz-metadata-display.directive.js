/*
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
   * @name horizon.framework.widgets.metadata-display.directive:hzMetadataDisplay
   * @scope
   *
   * @description
   * The `hzMetadataDisplay` displays existing metadata.
   *
   * @param {object[]} available List of available namespaces
   * @param {object} existing Key-value pairs with existing properties
   * @param {object=} text Text override
   */
  angular
    .module('horizon.framework.widgets.metadata-display')
    .directive('hzMetadataDisplay', hzMetadataDisplay);

  hzMetadataDisplay.$inject = ['horizon.framework.widgets.basePath'];

  function hzMetadataDisplay(path) {
    var directive = {
      controller: 'HzMetadataDisplayController as ctrl',
      scope: {
        available: '=',
        existing: '=',
        text: '=?'
      },
      templateUrl: path + 'metadata-display/metadata-display.html'
    };

    return directive;
  }
})();
