/*
 * (c) Copyright 2015 Hewlett-Packard Development Company, L.P.
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

(function () {
  "use strict";

  // NOTE: The javascript file being tested here isn't the magic-search code
  // as a whole, but instead the magic-overrides code.

  describe('MagicSearch module', function () {
    it('should be defined', function () {
      expect(angular.module('MagicSearch')).toBeDefined();
    });
  });

  describe('magic-overrides directive', function () {
    var $window, $scope, $magicScope, $element, $timeout;

    beforeEach(module('templates'));
    beforeEach(module('MagicSearch'));

    beforeEach(module(function ($provide) {
      $provide.value('$window', {
        location: {
          search: ''
        }
      });
    }));

    beforeEach(inject(function ($injector) {
      $window = $injector.get('$window');
      var $compile = $injector.get('$compile');
      $scope = $injector.get('$rootScope').$new();
      $timeout = $injector.get('$timeout');

      $scope.filterStrings = {
        cancel: gettext('Cancel'),
        prompt: gettext('Prompt'),
        remove: gettext('Remove'),
        text: gettext('Text')
      };

      $scope.filterFacets = [
        {
          name: 'name',
          label: gettext('Name'),
          singleton: true
        },
        {
          name: 'status',
          label: gettext('Status'),
          options: [
            { key: 'active', label: gettext('Active') },
            { key: 'shutdown', label: gettext('Shutdown') },
            { key: 'error', label: gettext('Error') }
          ]
        },
        {
          name: 'flavor',
          label: gettext('Flavor'),
          singleton: true,
          options: [
            { key: 'm1.tiny', label: gettext('m1.tiny') },
            { key: 'm1.small', label: gettext('m1.small') }
          ]
        }
      ];

      /* eslint-disable angular/ng_window_service */
      var markup =
        '<magic-search ' +
          'template="' + window.STATIC_URL + 'framework/widgets/magic-search/magic-search.html" ' +
          'strings="filterStrings" ' +
          'facets="{{ filterFacets }}">' +
        '</magic-search>';
      /* eslint-enable angular/ng_window_service */

      $element = $compile(angular.element(markup))($scope);

      $scope.$apply();

      $magicScope = $scope.$$childTail; //eslint-disable-line angular/ng_no_private_call

      spyOn($magicScope, '$emit');
      spyOn($magicScope, 'emitQuery');
      spyOn($magicScope, 'deleteFacetEntirely').and.callThrough();
      spyOn($magicScope, 'deleteFacetSelection').and.callThrough();
      spyOn($magicScope, 'initSearch');
      spyOn($magicScope, 'resetState');
    }));

    it('isMenuOpen should be initially false', function () {
      expect($magicScope.isMenuOpen).toBe(false);
    });

    it('isMenuOpen should be true after showMenu called', function () {
      $magicScope.showMenu();
      $timeout.flush();

      expect($magicScope.isMenuOpen).toBe(true);
    });

    it('isMenuOpen should be false after hideMenu called', function () {
      $magicScope.showMenu();
      $timeout.flush();
      $magicScope.hideMenu();
      $timeout.flush();

      expect($magicScope.isMenuOpen).toBe(false);
    });

    it('initSearch should be called when facetsChanged broadcasted', function () {
      $scope.$broadcast('facetsChanged');
      $timeout.flush();

      expect($magicScope.currentSearch).toEqual([]);
      expect($magicScope.initSearch).toHaveBeenCalled();
    });

    it('currentSearch should be empty when URL has no search terms', function () {
      expect($magicScope.currentSearch).toEqual([]);
    });

    describe('initFacets', function () {
      it('currentSearch should have one item when URL has one search term', function () {
        $window.location.search = '?name=myname';
        $magicScope.initFacets();
        $timeout.flush();

        expect($magicScope.currentSearch.length).toBe(1);
        expect($magicScope.currentSearch[0].label).toEqual([ 'Name', 'myname' ]);
        expect($magicScope.currentSearch[0].name).toBe('name=myname');
        expect($magicScope.strings.prompt).toBe('');

        // 'name' facet should be deleted (singleton)
        expect($magicScope.deleteFacetEntirely).toHaveBeenCalledWith([ 'name', 'myname' ]);
      });

      it('currentSearch should have two items when URL has two search terms', function () {
        $window.location.search = '?name=myname&status=active';
        $magicScope.initFacets();
        $timeout.flush();

        // only 'active' option should be removed from 'status' facet (not singleton)
        expect($magicScope.currentSearch.length).toBe(2);
        expect($magicScope.deleteFacetSelection).toHaveBeenCalledWith([ 'status', 'active' ]);
      });

      it('flavor facet should be removed if search term includes flavor', function () {
        $window.location.search = '?flavor=m1.tiny';
        $magicScope.initFacets();
        $timeout.flush();

        // entire 'flavor' facet should be removed even if some options left (singleton)
        expect($magicScope.deleteFacetEntirely).toHaveBeenCalledWith([ 'flavor', 'm1.tiny' ]);
      });

      it('currentSearch should have one item when search is textSearch', function () {
        $magicScope.textSearch = 'test';
        $magicScope.initFacets();

        expect($magicScope.currentSearch[0].label).toEqual([ 'Text', 'test' ]);
        expect($magicScope.currentSearch[0].name).toBe('text=test');
      });

      it('filteredObj should have two remaining items when URL has one search term', function () {
        $window.location.search = '?name=myname&status=active';
        $magicScope.initFacets();

        // filteredObj should have only unused facets and options
        // 'name' facet is singleton and should have been removed
        // 'status' facet is not single and should remain with one option left
        expect($magicScope.filteredObj.length).toBe(2);
      });

      it('should call checkFacets when initFacets called', function () {
        $magicScope.initFacets();

        expect($magicScope.$emit).toHaveBeenCalledWith('checkFacets', []);
      });
    });

    describe('removeFacet', function () {
      beforeEach(function () {
        spyOn($magicScope, 'initFacets');
      });

      it('should call emitQuery, initFacets and emit checkFacets on removeFacet', function () {
        var initialSearch = {
          name: 'name=myname',
          label: [ 'Name', 'myname' ]
        };
        $magicScope.currentSearch.push(initialSearch);
        $magicScope.removeFacet(0);

        expect($magicScope.currentSearch).toEqual([]);
        expect($magicScope.emitQuery).toHaveBeenCalledWith('name=myname');
        expect($magicScope.initFacets).toHaveBeenCalled();
        expect($magicScope.$emit).toHaveBeenCalledWith('checkFacets', []);
        expect($magicScope.strings.prompt).toBe('Prompt');
      });

      it('prompt text === "" if search terms left after removal of one', function () {
        $magicScope.strings.prompt = '';

        $magicScope.currentSearch.push({ name: 'name=myname', label: [ 'Name', 'myname' ] });
        $magicScope.currentSearch.push({ name: 'status=active', label: [ 'Status', 'Active' ] });
        $magicScope.removeFacet(0);

        expect($magicScope.strings.prompt).toBe('');
      });

      /*eslint-disable max-len */
      it('should call resetState, initFacets and emit checkFacets on removeFacet when facet selected',
      /*eslint-enable max-len */
        function () {
          var initialSearch = {
            name: 'name=myname',
            label: [ 'Name', 'myname' ]
          };
          $magicScope.currentSearch.push(initialSearch);
          $magicScope.facetSelected = {
            'name': 'status',
            'label': [ 'Status', 'active' ]
          };
          $magicScope.removeFacet(0);

          expect($magicScope.currentSearch).toEqual([]);
          expect($magicScope.resetState).toHaveBeenCalled();
          expect($magicScope.initFacets).toHaveBeenCalled();
          expect($magicScope.$emit).toHaveBeenCalledWith('checkFacets', []);
        }
      );
    });
  });

})();
