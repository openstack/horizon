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

  describe('search bar directive', function() {

    var $scope, $element;

    beforeEach(module('templates'));
    beforeEach(module('smart-table'));
    beforeEach(module('horizon.framework'));

    describe('search bar', function() {

      beforeEach(inject(function($injector) {
        var $compile = $injector.get('$compile');
        var $templateCache = $injector.get('$templateCache');
        var basePath = $injector.get('horizon.framework.widgets.basePath');
        $scope = $injector.get('$rootScope').$new();

        $scope.rows = [];

        var markup = $templateCache.get(basePath + 'table/st-table.mock.html');
        $element = angular.element(markup);
        $compile($element)($scope);

        $scope.$apply();
      }));

      it('should have a text field', function() {
        expect($element.find('input[st-search]').length).toBe(1);
      });

      it('should have a search icon', function() {
        expect($element.find('.input-group-addon .fa-search').length).toBe(1);
      });

      it('should have a "input-group-sm" class on input group', function() {
        expect($element.find('.input-group.input-group-sm').length).toBe(1);
      });

      it('should have default placeholder text set to "Filter"', function() {
        expect($element.find('input[st-search]').attr('placeholder')).toEqual('Filter');
      });

    });
  });
})();
