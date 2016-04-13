/*
 * (c) Copyright 2016 Hewlett Packard Enterprise Development Company LP
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
    .module('horizon.framework.widgets.magic-search')
    .directive('hzMagicSearchContext', hzMagicSearchContext);

  /**
   * @ngdoc directive
   * @name hzMagicSearchContext
   * @description
   * This directive provides a context for Magic Search features.
   * It encapsulates both the search element as well as the results
   * element to ensure that the results, and only the results that
   * are included in the context of this directive, are passed events.
   *
   * @restrict E
   * @scope
   *
   * @example
   * ```
   * <hz-magic-search-context>
   *   <magic-search
   *     template="/static/framework/widgets/magic-search/magic-search.html"
   *     strings="filterStrings"
   *     facets="{{ filterFacets }}">
   *   </magic-search>
   *   <table st-magic-search>
   *   </table>
   * </hz-magic-search-context>
   * ```
   */
  function hzMagicSearchContext() {
    var directive = {
      link: link,
      restrict: 'E',
      scope: true
    };
    return directive;

    function link(scope) {
      scope.$on('searchUpdated', resend);
      scope.$on('textSearch', resend);

      function resend(event, data) {
        scope.$broadcast(event.name + '-rebroadcast', data);
      }
    }
  }
})();
