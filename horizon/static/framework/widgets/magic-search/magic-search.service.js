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

(function() {
  'use strict';

  /**
   * @fileOverview Magic Search JS
   * @requires AngularJS
   *
   * Common terminology:
   *   Search Term - A single unit of a search as a string.  This is the
   *     minimal representation of a search.
   *     e.g. 'status=active'
   *
   *   Search Term Object - An object representation of a search term,
   *     e.g. {field: 'status', value: 'active'}
   *
   *   Facet - An object representing a unit of a search.  Includes the
   *     search term from above.  A search is composed of a list of facets.
   *     Note, this contains all the cross-referenced labels from the facet
   *     choice.
   *     e.g. {name: 'status=active', singleton=true,
   *           label: ['Status', 'Active']}
   *
   *   Facet Choice - An object representing a type of facet that can be used
   *     in a search.
   *     e.g. {name: 'status', singleton=true, options: [...]}
   *
   *   Option Choice - An object representing an option for a facet choice.
   *     e.g. {key: 'active', label: ['first', 'middle', 'last'] TODO check
   */

  angular.module('horizon.framework.widgets.magic-search')
    .factory('horizon.framework.widgets.magic-search.service', magicSearchService);

  magicSearchService.$inject = [];

  /**
   * @ngdoc service
   * @name horizon.framework.widgets.magic-search.service
   *
   * @returns the service.
   */
  function magicSearchService() {
    var service = {
      getFacetChoice: getFacetChoice,
      removeOptionChoice: removeOptionChoice,
      removeFacetChoice: removeFacetChoice,
      removeChoice: removeChoice,
      getEventCode: getEventCode,
      getFacet: getFacet,
      getSearchTermsFromQueryString: getSearchTermsFromQueryString,
      getFacetChoicesFromFacetsParam: getFacetChoicesFromFacetsParam,
      getFacetsFromSearchTerms: getFacetsFromSearchTerms,
      getSearchTermObject: getSearchTermObject,
      getMatchingFacets: getMatchingFacets,
      getMatchingOptions: getMatchingOptions,
      getName: getName,
      getTextFacet: getTextFacet,
      getUnusedFacetChoices: getUnusedFacetChoices,
      getQueryPattern: getQueryPattern
    };

    return service;

    // The following functions are primarily used to assist with various
    // map/reduce/filter uses in other functions.

    function objectify(obj) {
      return Object.create(obj);
    }

    function hasOptions(item) {
      return angular.isDefined(item.options);
    }

    function getTextFacet(searchVal, label) {
      return getFacet('text', searchVal, label, searchVal);
    }

    function getFacet(field, value, typeLabel, searchLabel) {
      return {'name': field + '=' + value, 'label': [typeLabel, searchLabel]};
    }

    function getSearchTermsFromQueryString(queryString) {
      return queryString.replace(/^\?/, '').split('&');
    }

    function getName(obj) {
      return obj.name;
    }

    function getQueryPattern(searchTermList) {
      return searchTermList.filter(isNotTextSearch).map(getName).join('&');

      function isNotTextSearch(item) {
        return item.name.indexOf('text') !== 0;
      }
    }

    function matchesName(name) {
      return function(facet) {
        return name === facet.name;
      };
    }

    function matchesKey(name) {
      return function(option) {
        return name === option.key;
      };
    }

    function hasLabel(item) {
      return angular.isDefined(item.label);
    }

    function getSearchTermObject(str) {
      var parts = str.split('=');
      return {type: parts[0], value: parts[1]};
    }

    // Given an item with a label, returns an array of three parts if the
    // string is a substring of the label.  Returns undefined if no match.
    // e.g.: 'searchforme', 'for' -> ['search', 'for', 'me']
    // Used to construct labels for options and facet choices based on
    // search terms.
    // TODO: not sure where the third element is used.
    function itemToLabel(item, search) {
      var idx = item.label.toLowerCase().indexOf(search);
      if (idx > -1) {
        return [item.label.substring(0, idx),
          item.label.substring(idx, idx + search.length),
          item.label.substring(idx + search.length)];
      }
    }

    // Helper function to more obviously perform the function
    // for the choice(s) in the facet list that match by name.
    // In theory there should only be one, but that's not enforceable.
    // The function should expect that the single parameter is the matching
    // choice.
    function execForMatchingChoice(facetChoices, name, func) {
      facetChoices.filter(matchesName(name)).forEach(func);
    }

    // Exposed functions

    function getEventCode(evt) {
      return evt.which || evt.keyCode || evt.charCode;
    }

    function getFacetChoice(orig) {
      var facetChoice = objectify(orig);
      // if there are options, copy their objects as well.  Expects a list.
      if (angular.isDefined(orig.options)) {
        facetChoice.options = orig.options.map(objectify);
      }
      return facetChoice;
    }

    // Translates options, returning only those that actually got labels
    // (those that matched the search).
    function getMatchingOptions(list, search) {
      return list.map(processOption).filter(hasLabel);

      function processOption(option) {
        return {'key': option.key, 'label':itemToLabel(option, search)};
      }
    }

    // Translates facets, returning only those that actually got labels
    // (those that matched the search).
    function getMatchingFacets(list, search) {
      return list.map(processFacet).filter(hasLabel);

      function processFacet(facet) {
        return {'name':facet.name, 'label':itemToLabel(facet, search),
          'options':facet.options};
      }
    }

    function getFacetChoicesFromFacetsParam(param) {
      if (angular.isString(param)) {
        // Parse facets JSON and convert to a list of facets.
        var tmp = param.replace(/__apos__/g, "\'")
          .replace(/__dquote__/g, '\\"')
          .replace(/__bslash__/g, "\\");
        return angular.fromJson(tmp);
      }

      // Assume this is a usable javascript object
      return param;
    }

    // Takes in search terms in the form of field=value, ...
    // then returns a list of facets, complete with
    // labels.  Basically, a merge of data from the current search
    // and the facet choices.
    function getFacetsFromSearchTerms(searchTerms, textSearch, textSearchLabel, facetChoices) {
      var buff = [];
      searchTerms.map(getSearchTermObject).forEach(getFacetFromObj);
      if (angular.isDefined(textSearch)) {
        var currentTextSearch = searchTerms.filter(function(searchField) {
          return searchField.indexOf(textSearch) === 0;
        });
        if (currentTextSearch.length === 0) {
          buff.push(getTextFacet(textSearch, textSearchLabel));
        }
      }
      return buff;

      function getFacetFromObj(searchTermObj) {
        execForMatchingChoice(facetChoices, searchTermObj.type, addFacet);

        function addFacet(facetChoice) {
          if (angular.isUndefined(facetChoice.options)) {
            buff.push(getFacet(searchTermObj.type, searchTermObj.value,
              facetChoice.label, searchTermObj.value));
          } else {
            facetChoice.options.filter(matchesKey(searchTermObj.value)).forEach(function (option) {
              buff.push(getFacet(searchTermObj.type, searchTermObj.value,
                facetChoice.label, option.label));
            });
          }
        }
      }
    }

    // The rest of the functions have to do entirely with removing
    // facets from the choices that are presented to the user.

    // Retrieves Facet Choices and returns only those not used in the
    // given facets (those not in the current search).
    function getUnusedFacetChoices(facetChoices, facets) {
      var unused = angular.copy(facetChoices);
      facets.map(getSearchTermObject).forEach(processSearchTerm);
      return unused;

      function processSearchTerm(searchTerm) {
        // finds any/all matching choices (should only be one)
        execForMatchingChoice(unused, searchTerm.type, removeFoundChoice);

        function removeFoundChoice(choice) {
          if (angular.isUndefined(choice.options)) {

            // for refresh case, need to remove facets that were
            // bookmarked/current when browser refresh was clicked
            removeFacetChoice(searchTerm.type, unused);

          } else if (choice.options.some(matchesKey(searchTerm.value))) {
            removeSingleChoice(choice, searchTerm, unused);
          }
        }
      }
    }

    // remove entire facet choice
    function removeFacetChoice(type, target) {
      execForMatchingChoice(target.slice(), type, removeFacet);

      function removeFacet(facet) {
        target.splice(target.indexOf(facet), 1);
      }
    }

    // Removes a choice from the target, based on the values in the search
    // term object.  If the choice is of type 'singleton', the entire
    // facet choice is removed; otherwise it removes the choice's option.
    function removeSingleChoice(facetChoice, searchTermObj, target) {
      if (facetChoice.singleton === true) {
        removeFacetChoice(searchTermObj.type, target);
      } else {
        removeOptionChoice(searchTermObj, target);
      }
    }

    // Removes an item from the given target list; uses src (list of the types)
    // so it may reference whether the type is a singleton or not.
    function removeChoice(searchTerm, src, target) {
      execForMatchingChoice(src, searchTerm.type, removeFacetOrOption);

      function removeFacetOrOption(facet) {
        removeSingleChoice(facet, searchTerm, target);
      }
    }

    // Removes an option from a facet choice, based on a search term object.
    function removeOptionChoice(searchTermObj, target) {
      execForMatchingChoice(target.slice().filter(hasOptions),
        searchTermObj.type, removeOption);

      function removeOption(choice) {
        // Slim down choices based on key match.
        choice.options = choice.options.filter(keyNotMatch(searchTermObj.value));

        // If there are no remaining options for this choice, remove the
        // choice entirely.
        if (choice.options.length === 0) {
          // Manipulating a list that it's going through.
          // This happens to work due to how it is iterated and searched
          // but arguably is not ideal. We want to retain the original
          // array object due to references elsewhere.
          target.splice(target.indexOf(choice), 1);
        }

        function keyNotMatch(value) {
          return function keyNotMatchBool(option) {
            return option.key !== value;
          };
        }
      }
    }
  }

})();
