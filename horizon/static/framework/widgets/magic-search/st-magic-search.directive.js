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
    .directive('stMagicSearch', stMagicSearch);

  stMagicSearch.$inject = ['$timeout'];

  /**
   * @ngdoc directive
   * @name MagicSearch.directive:stMagicSearch
   * @element
   * @description
   * A directive to make Magic Search be a replacement for st-search.
   * This directive must be outside of a magic-search and inside a
   * smart-table. This lets MS drive the same filtering capabilities
   * in smart-table that st-search does, including filtering on all
   * columns or a specific column (e.g. a facet filters a column).
   *
   * @restrict E
   * @scope
   *
   * @example
   * ```
   * <st-magic-search>
   *   <magic-search
   *     template="/static/framework/widgets/magic-search/magic-search.html"
   *     strings="filterStrings"
   *     facets="{{ filterFacets }}">
   *   </magic-search>
   * </st-magic-search>
   * ```
   */
  function stMagicSearch($timeout) {
    var directive = {
      link: link,
      require: '^stTable',
      restrict: 'E',
      scope: true
    };
    return directive;

    function link(scope, element, attr, tableCtrl) {
      var clientFullTextSearch = (angular.isDefined(scope.clientFullTextSearch)
                                  ? scope.clientFullTextSearch
                                  : true);

      scope.currentServerSearchParams = {};

      // Generate predicate object from dot notation string
      function setPredObj(predicates, predObj, input) {
        var lastPred = predicates.pop();

        angular.forEach(predicates, function(pred) {
          predObj = predObj[pred] = {};
        });

        predObj[lastPred] = input;
      }

      function setServerFacetSearch(scope, query) {
        var currentServerSearchParams = angular.copy(scope.currentServerSearchParams);
        currentServerSearchParams.magicSearchQuery = query;
        checkAndEmit(scope, currentServerSearchParams);
      }

      function setServerTextSearch(scope, text) {
        var currentServerSearchParams = angular.copy(scope.currentServerSearchParams);
        currentServerSearchParams.queryString = text;
        checkAndEmit(scope, currentServerSearchParams);
      }

      function checkAndEmit(scope, serverSearchParams) {
        if (serverSearchParams !== scope.currentServerSearchParams) {
          serverSearchParams.magicSearchQueryChanged =
            !angular.equals(scope.currentServerSearchParams.magicSearchQuery,
                            serverSearchParams.magicSearchQuery);

          serverSearchParams.queryStringChanged =
            !angular.equals(scope.currentServerSearchParams.queryString,
                            serverSearchParams.queryString);

          scope.currentServerSearchParams = serverSearchParams;

          if (serverSearchParams.queryStringChanged || serverSearchParams.magicSearchQueryChanged) {
            scope.$emit('serverSearchUpdated', angular.copy(scope.currentServerSearchParams));
          }
        }
      }

      // When user types a character, search the table
      var textSearchWatcher = scope.$on('textSearch', function(event, text) {
        // Timeout needed to prevent
        // $apply already in progress error
        $timeout(function() {
          if (clientFullTextSearch) {
            tableCtrl.search(text);
          } else {
            setServerTextSearch(scope, text);
          }
        });
      });

      // When user changes a facet, use API filter
      var searchUpdatedWatcher = scope.$on('searchUpdated', function(event, query) {
        setServerFacetSearch(scope, query);

        // clear each time since Smart-Table
        // search is cumulative
        tableCtrl.tableState().search = {};

        // filter the smart table per column
        query.split('&').forEach(function(x) {
          $timeout(function() {
            var arr = x.split('=');
            var predString = arr[0];
            var predicates = predString.split('.');

            if (scope.filterFacets) {
              var isServerFacet = scope.filterFacets.some(function checkIsServer(facet) {
                return facet.name === predString && facet.isServer;
              });

              if (isServerFacet) {
                return;
              }
            }

            // Allow nested property search
            if (predicates.length > 1) {
              var firstPred = predicates[0];

              var predicateObj = {};
              setPredObj(predicates, predicateObj, arr[1]);

              tableCtrl.search(predicateObj[firstPred], firstPred);
            } else {
              tableCtrl.search(arr[1], predString);
            }
          });
        });
      });

      scope.$on('$destroy', function () {
        textSearchWatcher();
        searchUpdatedWatcher();
      });
    }
  }
})();
