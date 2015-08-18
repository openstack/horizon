/*
 * (c) Copyright 2015 Hewlett-Packard Development Company, L.P.
 * Copyright 2015 IBM Corp.
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

  describe('transfer-table directive', function() {

    beforeEach(module('templates'));
    beforeEach(module('smart-table'));
    beforeEach(module('horizon.framework'));

    var $templateCache, $compile, $scope, basePath;
    var available = [
      { id: '1', animal: 'cat' },
      { id: '2', animal: 'dog' },
      { id: '3', animal: 'fish' }
    ];

    beforeEach(inject(function($injector) {
      basePath = $injector.get('horizon.framework.widgets.basePath');
      $templateCache = $injector.get('$templateCache');
      $compile = $injector.get('$compile');
      $scope = $injector.get('$rootScope').$new();
      $scope.tableData = {
        available: available,
        allocated: [],
        displayedAvailable: [].concat(available),
        displayedAllocated: []
      };
    }));

    describe('render with allocated and available tags', function() {

      var $element;
      beforeEach(inject(function($injector) {
        var path = 'transfer-table/transfer-table.basic.mock.html';
        var markup = $templateCache.get(basePath + path);
        $element = angular.element(markup);
        $compile($element)($scope);
        $scope.$apply();
      }));

      it('should place allocated and available element correctly', testContent);
      it('should have 0 allocated rows', testAllocatedRows);
      it('should have 3 available rows', testAvailableRows);

      ///////////

      function testContent() {
        expect($element.find('table').length).toBe(2);
        expect($element.find('.transfer-allocated > allocated').length).toBe(1);
        expect($element.find('.transfer-available > available').length).toBe(1);
      }

      function testAllocatedRows() {
        expect($element.find('.transfer-allocated tr[ng-repeat]').length).toBe(0);
      }

      function testAvailableRows() {
        expect($element.find('.transfer-available tr[ng-repeat]').length).toBe(3);
      }

    });

    describe('clone content', function() {

      var $element;
      beforeEach(inject(function($injector) {
        var path = 'transfer-table/transfer-table.clone.mock.html';
        var markup = $templateCache.get(basePath + path);
        $element = angular.element(markup);
        $compile($element)($scope);
        $scope.$apply();
      }));

      it('should contain 2 table elements', testCloneContent);
      it('should have 0 allocated rows', testAllocatedRows);
      it('should have 3 available rows', testAvailableRows);
      it('should create 2 new scopes', testNewScopes);

      ///////////

      function testCloneContent() {
        expect($element.find('table').length).toBe(2);
        expect($element.find('.transfer-allocated > table').length).toBe(1);
        expect($element.find('.transfer-available > table').length).toBe(1);
      }

      function testAllocatedRows() {
        expect($element.find('.transfer-allocated tr[ng-repeat]').length).toBe(0);
      }

      function testAvailableRows() {
        expect($element.find('.transfer-available tr[ng-repeat]').length).toBe(3);
      }

      function testNewScopes() {
        var allocatedScope = $element.find('.transfer-allocated > table').scope();
        var availableScope = $element.find('.transfer-available > table').scope();
        expect(allocatedScope.$isAllocatedTable).toBe(true);
        expect(allocatedScope.$sourceItems).toBe($scope.tableData.allocated);
        expect(allocatedScope.$displayedItems).toBe($scope.tableData.displayedAllocated);
        expect(availableScope.$isAvailableTable).toBe(true);
        expect(availableScope.$sourceItems).toBe($scope.tableData.available);
        expect(availableScope.$displayedItems).toBe($scope.tableData.displayedAvailable);
      }

    });

  }); // end of transfer-table directive
})(); // end of IIFE
