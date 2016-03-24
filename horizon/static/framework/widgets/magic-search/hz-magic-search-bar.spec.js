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

  describe('hz-magic-search-bar directive', function () {
    var $element, $scope, $compile;

    beforeEach(module('templates'));
    beforeEach(module('smart-table'));
    beforeEach(module('horizon.framework'));
    beforeEach(module('horizon.framework.widgets.magic-search'));

    beforeEach(inject(function ($injector) {
      $compile = $injector.get('$compile');
      $scope = $injector.get('$rootScope').$new();

      $scope.rows = [];

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

      var searchBar =
                   '     <hz-magic-search-bar ' +
                   '       filter-facets="filterFacets" ' +
                   '       filter-strings="filterStrings">' +
                   '     </hz-magic-search-bar>';
      var markup = searchBar + '<table st-table="rows" st-magic-search>' +
                   '<thead>' +
                   ' <tr>' +
                   '   <th>' +
                   '   </th>' +
                   ' </tr>' +
                   '</thead>' +
                   '<tbody></tbody>' +
                   '</table>';

      $element = $compile(angular.element(markup))($scope);

      $scope.$apply();
    }));

    it('magic-search should be defined', function () {
      var searchBar = $element.find('magic-search');
      expect(searchBar.length).toBe(1);
    });

    it('use filterStrings defaults if not provided as attribute', function () {
      var markup = '<table st-table="rows">' +
                   '<thead>' +
                   ' <tr>' +
                   '   <th>' +
                   '     <hz-magic-search-bar ' +
                   '       filter-facets="filterFacets">' +
                   '     </hz-magic-search-bar>' +
                   '   </th>' +
                   ' </tr>' +
                   '</thead>' +
                   '<tbody></tbody>' +
                   '</table>';

      $element = $compile(angular.element(markup))($scope);
      $scope.$apply();

      var filterStrings = $element.find('magic-search').attr('strings');
      expect(filterStrings).toBeDefined();
    });
  });
})();
