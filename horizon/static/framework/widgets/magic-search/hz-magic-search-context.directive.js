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

  hzMagicSearchContext.$inject = ['$parse'];

  /**
   * @ngdoc directive
   * @name hzMagicSearchContext
   * @description
   * This directive provides a context for Magic Search features.
   * It encapsulates both the search element as well as the results
   * element to ensure that the results, and only the results that
   * are included in the context of this directive, are passed events.
   *
   * The context 'relays' events back down to constituent components
   * by appending '-ms-context' to them to avoid infinite-loop situations.
   * This allows controls to clearly distinguish direct events and those
   * coming from the context directive.
   *
   * @param {object} filterFacets Facets allowed for searching
   * @param {object=} filterStrings Help content shown in search bar
   * @param {object=} clientFullTextSearch if full text search is to be done on the client
   * Facets:
   * ```
   * var nameFacet = {
   *   label: gettext('Name'),
   *   name: 'name',
   *   singleton: true
   * };
   *
   * var sizeFacet = {
   *   label: gettext('Size'),
   *   name: 'size',
   *   singleton: false,
   *   options: [
   *     { label: gettext('Small'), key: 'small' },
   *     { label: gettext('Medium'), key: 'medium' },
   *     { label: gettext('Large'), key: 'large' },
   *   ]
   * };
   * ```
   *
   * label - this is the text shown in top level facet dropdown menu
   * name - this is the column key provided to Smart-Table
   * singleton - 'true' if free text can be used as search term
   * options - list of options shown in selected facet dropdown menu
   * @restrict E
   * @scope
   *
   * @example
   * ```
   * <hz-magic-search-context
   *   template="/static/framework/widgets/magic-search/magic-search.html"
   *   strings="filterStrings"
   *   facets="{{ filterFacets }}">
   *   <magic-search></magic-search>
   *   <table st-magic-search st-table="controller.data">
   *   </table>
   * </hz-magic-search-context>
   * ```
   */
  function hzMagicSearchContext($parse) {
    var directive = {
      link: link,
      restrict: 'E',
      scope: true
    };
    return directive;

    function link(scope, element, attrs) {
      var filterStrings = $parse(attrs.filterStrings)(scope);
      var filterFacets = $parse(attrs.filterFacets)(scope);
      var clientFullTextSearch = $parse(attrs.clientFullTextSearch)(scope);
      var searchSettingsCallback = $parse(attrs.searchSettingsCallback)(scope);
      scope.filterFacets = filterFacets;
      scope.searchSettingsCallback = searchSettingsCallback;

      scope.clientFullTextSearch = angular.isDefined(clientFullTextSearch)
        ? clientFullTextSearch
        : true;
      // if filterStrings is not defined, set defaults
      var defaultFilterStrings = {
        cancel: gettext('Cancel'),
        prompt: gettext('Click here for filters.'),
        remove: gettext('Remove'),
        text: (scope.clientFullTextSearch
          ? gettext('Search in current results')
          : gettext('Full Text Search'))
      };
      scope.filterStrings = filterStrings || defaultFilterStrings;

      if (angular.isDefined(searchSettingsCallback)) {
        scope.showSettings = true;
      } else {
        scope.showSettings = false;
      }

      scope.$on('searchUpdated', resend);
      scope.$on('textSearch', resend);
      scope.$on('checkFacets', resend);
      scope.$on('facetsChanged', resend);
      scope.$on('serverSearchUpdated', resend);

      function resend(event, data) {
        scope.$broadcast(event.name + '-ms-context', data);
      }
    }
  }
})();
