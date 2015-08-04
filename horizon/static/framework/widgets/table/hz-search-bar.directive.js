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
    .directive('hzSearchBar', hzSearchBar);

  hzSearchBar.$inject = [
    'horizon.framework.widgets.table.filterPlaceholderText',
    'horizon.framework.widgets.basePath'
  ];

  /**
   * @ngdoc directive
   * @name horizon.framework.widgets.table.directive:hzSearchBar
   * @element
   * @param {string} {array} groupClasses Input group classes (optional)
   * @param {string} {array} iconClasses Icon classes (optional)
   * @param {string} {array} inputClasses Search field classes (optional)
   * @param {string} placeholder input field placeholder text (optional)
   * @description
   * The `hzSearchBar` directive generates a search field that will
   * trigger filtering of the associated Smart-Table.
   *
   * groupClasses - classes that should be applied to input group element
   * iconClasses - classes that should be applied to search icon
   * inputClasses - classes that should be applied to search input field
   * placeholder - text that will be used for a placeholder attribute
   *
   * @restrict E
   *
   * @example
   * ```
   * <hz-search-bar group-classes="input-group-sm"
   *   icon-classes="fa-search" input-classes="..." placeholder="Filter">
   * </hz-search-bar>
   * ```
   */
  function hzSearchBar(FILTER_PLACEHOLDER_TEXT, basePath) {

    var directive = {
      restrict: 'E',
      templateUrl: basePath + 'table/search-bar.html',
      transclude: true,
      link: link
    };
    return directive;

    ////////////////////

    function link(scope, element, attrs, ctrl, transclude) {
      if (angular.isDefined(attrs.groupClasses)) {
        element.find('.input-group').addClass(attrs.groupClasses);
      }
      if (angular.isDefined(attrs.iconClasses)) {
        element.find('.fa').addClass(attrs.iconClasses);
      }
      var searchInput = element.find('[st-search]');

      if (angular.isDefined(attrs.inputClasses)) {
        searchInput.addClass(attrs.inputClasses);
      }
      var placeholderText = attrs.placeholder || FILTER_PLACEHOLDER_TEXT;
      searchInput.attr('placeholder', placeholderText);

      transclude(scope, function(clone) {
        element.find('.input-group').append(clone);
      });
    }
  }
}());
