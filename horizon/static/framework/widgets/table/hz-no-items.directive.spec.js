/*
 * Copyright 2015 IBM Corp.
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

  function digestMarkup(scope, compile, markup) {
    var element = angular.element(markup);
    compile(element)(scope);

    scope.$apply();
    return element;
  }

  describe('hzNoItems directive', function() {
    var $scope, $compile, $templateCache, markup;

    beforeEach(module('templates'));
    beforeEach(module('smart-table'));
    beforeEach(module('horizon.framework'));

    beforeEach(inject(function($injector) {
      $compile = $injector.get('$compile');
      $scope = $injector.get('$rootScope').$new();

      $scope.safeTableData = [
        { id: '1', animal: 'cat' },
        { id: '2', animal: 'dog' },
        { id: '3', animal: 'fish' }
      ];

      $scope.fakeTableData = [];

      var basePath = $injector.get('horizon.framework.widgets.basePath');
      $templateCache = $injector.get('$templateCache');
      markup = $templateCache.get(basePath + 'table/no-items.mock.html');
    }));

    it('has 3 rows and 0 no-rows message when there are users in the table', function() {
      var $element = digestMarkup($scope, $compile, markup);

      expect($element).toBeDefined();
      expect($element.find('tbody td.no-rows-help').length).toBe(0);
    });

    it('has 0 rows and 1 no-rows message when there are no users in the table', function() {
      $scope.safeTableData = [];
      $scope.fakeTableData = [];

      var $element = digestMarkup($scope, $compile, markup);

      expect($element.find('tbody td.no-rows-help').length).toBe(1);
      expect($element.find('tbody td.no-rows-help').text()).toBe('No items to display.');
    });

    it('has 0 rows and 1 custom no-rows message when there are no users in the table', function() {
      $scope.message = 'No pets to display.';
      $scope.safeTableData = [];
      $scope.fakeTableData = [];

      var $element = digestMarkup($scope, $compile, markup);

      expect($element.find('tbody td.no-rows-help').length).toBe(1);
      expect($element.find('tbody td.no-rows-help').text()).toBe('No pets to display.');
    });

  });
}());
