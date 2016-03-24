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
 */

  angular.module('horizon.framework.widgets.magic-search')
    .controller('MagicSearchController', magicSearchController);

  magicSearchController.$inject = ['$scope', '$element', '$timeout', '$window',
    'horizon.framework.widgets.magic-search.service'];

  function magicSearchController($scope, $element, $timeout, $window, service) {
    var ctrl = this;
    var searchInput = $element.find('.search-input');
    ctrl.mainPromptString = $scope.strings.prompt;

    // currentSearch is the list of facets representing the current search
    ctrl.currentSearch = [];
    ctrl.isMenuOpen = false;

    searchInput.on('keydown', keyDownHandler);
    searchInput.on('keyup', keyUpHandler);
    searchInput.on('keypress', keyPressHandler);

    // enable text entry when mouse clicked anywhere in search box
    $element.find('.search-main-area').on('click', searchMainClickHandler);

    // when facet clicked, add 1st part of facet and set up options
    ctrl.facetClicked = facetClickHandler;

    // when option clicked, complete facet and send event
    ctrl.optionClicked = optionClickHandler;

    // remove facet and either update filter or search
    ctrl.removeFacet = removeFacet;

    // Controller-exposed Functions
    // clear entire searchbar
    ctrl.clearSearch = clearSearch;

    // ctrl.textSearch is undefined, only used when a user free-enters text

    // Used by the template.
    ctrl.isMatchLabel = function(label) {
      return angular.isArray(label);
    };

    // unusedFacetChoices is the list of facet types that have not been selected
    ctrl.unusedFacetChoices = [];

    // facetChoices is the list of all facet choices
    ctrl.facetChoices = [];

    initSearch(service.getSearchTermsFromQueryString($window.location.search));
    emitQuery();

    function initSearch(initialSearchTerms) {
      // Initializes both the unused choices and the full list of facets
      ctrl.facetChoices = service.getFacetChoicesFromFacetsParam($scope.facets_param);

      // resets the facets
      initFacets(initialSearchTerms);
    }

    function keyDownHandler($event) {
      var key = service.getEventCode($event);
      if (key === 9) {  // prevent default when we can.
        $event.preventDefault();
      }
    }

    function tabKeyUp() {
      if (angular.isUndefined(ctrl.facetSelected)) {
        if (ctrl.filteredObj.length !== 1) {
          return;
        }
        ctrl.facetClicked(0, '', ctrl.filteredObj[0].name);
        setSearchInput('');
      } else {
        if (angular.isUndefined(ctrl.filteredOptions) ||
          ctrl.filteredOptions.length !== 1) {
          return;
        }
        ctrl.optionClicked(0, '', ctrl.filteredOptions[0].key);
        resetState();
      }
    }

    function escapeKeyUp() {
      setMenuOpen(false);
      resetState();
      var textFilter = ctrl.textSearch;
      if (angular.isUndefined(textFilter)) {
        textFilter = '';
      }
      emitTextSearch(textFilter);
    }

    function enterKeyUp() {
      var searchVal = searchInput.val();
      // if tag search, treat as regular facet
      if (ctrl.facetSelected && angular.isUndefined(ctrl.facetSelected.options)) {
        var curr = ctrl.facetSelected;
        curr.name = curr.name.split('=')[0] + '=' + searchVal;
        curr.label[1] = searchVal;
        ctrl.currentSearch.push(curr);
        resetState();
        emitQuery();
        setMenuOpen(false);
      } else {
        // if text search treat as search
        ctrl.currentSearch = ctrl.currentSearch.filter(notTextSearch);
        ctrl.currentSearch.push(service.getTextFacet(searchVal, $scope.strings.text));
        $scope.$apply();
        setMenuOpen(false);
        setSearchInput('');
        emitTextSearch(searchVal);
        ctrl.textSearch = searchVal;
      }
      ctrl.filteredObj = ctrl.unusedFacetChoices;
    }

    function notTextSearch(item) {
      return item.name.indexOf('text') !== 0;
    }

    function defaultKeyUp() {
      var searchVal = searchInput.val();
      if (searchVal === '') {
        ctrl.filteredObj = ctrl.unusedFacetChoices;
        $scope.$apply();
        emitTextSearch('');
        if (ctrl.facetSelected && angular.isUndefined(ctrl.facetSelected.options)) {
          resetState();
        }
      } else {
        filterFacets(searchVal);
      }
    }

    function keyUpHandler($event) {  // handle ctrl-char input
      if ($event.metaKey === true) {
        return;
      }
      var key = service.getEventCode($event);
      var handlers = { 9: tabKeyUp, 27: escapeKeyUp, 13: enterKeyUp };
      if (handlers[key]) {
        handlers[key]();
      } else {
        defaultKeyUp();
      }
    }

    function keyPressHandler($event) {  // handle character input
      var searchVal = searchInput.val();
      var key = service.getEventCode($event);
      // Backspace, Delete, Enter, Tab, Escape
      if (key !== 8 && key !== 46 && key !== 13 && key !== 9 && key !== 27) {
        // This builds the search term as you go.
        searchVal = searchVal + String.fromCharCode(key).toLowerCase();
      }
      if (searchVal === ' ') {  // space and field is empty, show menu
        setMenuOpen(true);
        setSearchInput('');
        return;
      }
      if (searchVal === '') {
        ctrl.filteredObj = ctrl.unusedFacetChoices;
        $scope.$apply();
        emitTextSearch('');
        if (ctrl.facetSelected && angular.isUndefined(ctrl.facetSelected.options)) {
          resetState();
        }
        return;
      }
      // Backspace, Delete
      if (key !== 8 && key !== 46) {
        filterFacets(searchVal);
      }
    }

    function filterFacets(searchVal) {
      // try filtering facets/options.. if no facets match, do text search
      var filtered = [];
      var isTextSearch = angular.isUndefined(ctrl.facetSelected);
      if (isTextSearch) {
        ctrl.filteredObj = ctrl.unusedFacetChoices;
        filtered = service.getMatchingFacets(ctrl.filteredObj, searchVal);
      } else {  // assume option search
        ctrl.filteredOptions = ctrl.facetOptions;
        if (angular.isUndefined(ctrl.facetOptions)) {
          // no options, assume free form text facet
          return;
        }
        filtered = service.getMatchingOptions(ctrl.filteredOptions, searchVal);
      }
      if (filtered.length > 0) {
        setMenuOpen(true);
        $timeout(function() {
          ctrl.filteredObj = filtered;
        }, 0.1);
      } else if (isTextSearch) {
        emitTextSearch(searchVal);
        setMenuOpen(false);
      }
    }

    function searchMainClickHandler($event) {
      var target = angular.element($event.target);
      if (target.is('.search-main-area')) {
        searchInput.trigger('focus');
        setMenuOpen(true);
      }
    }

    function facetClickHandler($index) {
      setMenuOpen(false);
      var facet = ctrl.filteredObj[$index];
      var label = facet.label;
      if (angular.isArray(label)) {
        label = label.join('');
      }
      var facetParts = facet.name && facet.name.split('=');
      ctrl.facetSelected = service.getFacet(facetParts[0], facetParts[1], label, '');
      if (angular.isDefined(facet.options)) {
        ctrl.filteredOptions = ctrl.facetOptions = facet.options;
        setMenuOpen(true);
      }
      setSearchInput('');
      setPrompt('');
      $timeout(function() {
        searchInput.focus();
      });
    }

    function optionClickHandler($index, $event, name) {
      setMenuOpen(false);
      var curr = ctrl.facetSelected;
      curr.name = curr.name.split('=')[0] + '=' + name;
      curr.label[1] = ctrl.filteredOptions[$index].label;
      if (angular.isArray(curr.label[1])) {
        curr.label[1] = curr.label[1].join('');
      }
      ctrl.currentSearch.push(curr);
      resetState();
      emitQuery();
    }

    function emitTextSearch(val) {
      $scope.$emit('textSearch', val, $scope.filter_keys);
    }

    function emitQuery(removed) {
      var query = service.getQueryPattern(ctrl.currentSearch);
      if (angular.isDefined(removed) && removed.indexOf('text') === 0) {
        emitTextSearch('');
        delete ctrl.textSearch;
      } else {
        $scope.$emit('searchUpdated', query);
        if (ctrl.currentSearch.length > 0) {
          // prune facets as needed from menus
          var newFacet = ctrl.currentSearch[ctrl.currentSearch.length - 1].name;
          var facetParts = service.getSearchTermObject(newFacet);
          service.removeChoice(facetParts, ctrl.facetChoices, ctrl.unusedFacetChoices);
        }
      }
    }

    function clearSearch() {
      if (ctrl.currentSearch.length > 0) {
        ctrl.currentSearch = [];
        ctrl.unusedFacetChoices = ctrl.facetChoices.map(service.getFacetChoice);
        resetState();
        $scope.$emit('searchUpdated', '');
        emitTextSearch('');
      }
    }

    function resetState() {
      setSearchInput('');
      ctrl.filteredObj = ctrl.unusedFacetChoices;
      delete ctrl.facetSelected;
      delete ctrl.facetOptions;
      delete ctrl.filteredOptions;
      if (ctrl.currentSearch.length === 0) {
        setPrompt(ctrl.mainPromptString);
      }
    }

    function setMenuOpen(bool) {
      $timeout(function setMenuOpenTimeout() {
        ctrl.isMenuOpen = bool;
      });
    }

    function setSearchInput(val) {
      $timeout(function setSearchInputTimeout() {
        searchInput.val(val);
      });
    }

    function setPrompt(str) {
      $timeout(function setPromptTimeout() {
        $scope.strings.prompt = str;
      });
    }

    /**
     * Add ability to update facet
     * Broadcast event when facet options are returned via AJAX.
     * Should magic_search.js absorb this?
     */
    var facetsChangedWatcher = $scope.$on('facetsChanged', function (event, data) {
      $timeout(function () {
        if (data && data.magicSearchQuery) {
          initSearch(data.magicSearchQuery.split('&'));
        } else {
          initSearch(ctrl.currentSearch.map(function(x) { return x.name; }));
        }
      });
    });

    $scope.$on('$destroy', function () {
      facetsChangedWatcher();
    });

    function initFacets(searchTerms) {
      var tmpFacetChoices = ctrl.facetChoices.map(service.getFacetChoice);
      if (searchTerms.length > 1 || searchTerms[0] && searchTerms[0].length > 0) {
        setPrompt('');
      }
      ctrl.currentSearch = service.getFacetsFromSearchTerms(searchTerms,
        ctrl.textSearch, $scope.strings.text, tmpFacetChoices);
      ctrl.filteredObj = ctrl.unusedFacetChoices =
        service.getUnusedFacetChoices(tmpFacetChoices, searchTerms);

      // emit to check facets for server-side
      $scope.$emit('checkFacets', ctrl.currentSearch);
    }

    /**
     * Override magic_search.js 'removeFacet' to emit('checkFacets')
     * to flag facets as 'isServer' after removing facet and
     * either update filter or search
     * @param {number} index - the index of the facet to remove. Required.
     *
     * @returns {number} Doesn't return anything
     */
    function removeFacet(index) {
      var removed = ctrl.currentSearch[index].name;
      ctrl.currentSearch.splice(index, 1);
      if (angular.isUndefined(ctrl.facetSelected)) {
        emitQuery(removed);
      } else {
        resetState();
      }
      if (ctrl.currentSearch.length === 0) {
        setPrompt(ctrl.mainPromptString);
      }
      // re-init to restore facets cleanly
      initFacets(ctrl.currentSearch.map(service.getName));
    }

  }

})();
