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

  angular
    .module('horizon.framework.widgets.magic-search')
    .directive('hzMagicSearchBar', hzMagicSearchBar);

  hzMagicSearchBar.$inject = ['horizon.framework.widgets.basePath'];

  /**
   * @ngdoc directive
   * @name MagicSearch.directive:hzMagicSearchBar
   * @element
   * @description
   * The `magicSearchBar` directive provides a template for a
   * client side faceted search that utilizes Smart-Table's
   * filtering capabilities as well.  It needs to be placed within
   * an hz-magic-search-context to be effective.
   *
   * @restrict E
   * @scope
   *
   * @example
   * ```
   * <hz-magic-search-context>
   *   <hz-magic-search-bar></hz-magic-search-bar>
   * </hz-magic-search-context>
   * ```
   */
  function hzMagicSearchBar(basePath) {

    var directive = {
      compile: compile,
      restrict: 'E',
      scope: true,
      templateUrl: basePath + 'magic-search/hz-magic-search-bar.html'
    };

    return directive;

    //////////

    function link() {
    }

    function compile(element) {
      /**
       * Need to set template here since MagicSearch template
       * attribute is not interpolated. Can't hardcode the
       * template location and need to use basePath.
       */
      var templateUrl = basePath + 'magic-search/magic-search.html';
      element.find('magic-search').attr('template', templateUrl);
      element.addClass('hz-magic-search-bar');
      return link;
    }
  }

})();
