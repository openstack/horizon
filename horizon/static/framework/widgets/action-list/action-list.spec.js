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
(function () {
  'use strict';

  describe('horizon.framework.widgets.action-list module', function () {
    it('should have been defined', function () {
      expect(angular.module('horizon.framework.widgets.action-list')).toBeDefined();
    });
  });

  describe('action-list directive', function () {
    beforeEach(module('templates'));
    beforeEach(module('horizon.framework'));

    describe('single button dropdown', function () {
      var $scope, $element;

      beforeEach(inject(function ($injector) {
        var $compile = $injector.get('$compile');
        var $templateCache = $injector.get('$templateCache');
        var basePath = $injector.get('horizon.framework.widgets.basePath');

        $scope = $injector.get('$rootScope').$new();

        $scope.testList = [];
        $scope.item = 'test';

        $scope.clickMe = function (item) {
          $scope.testList.push(item);
        };

        var markup = $templateCache
          .get(basePath + 'action-list/action-list.single-button-dropdown.mock.html');

        $element = angular.element(markup);
        $compile($element)($scope);

        $scope.$apply();
      }));

      it('should have one dropdown button', function () {
        var dropdownButton = $element.find('.single-button');
        expect(dropdownButton.length).toBe(1);
        expect(dropdownButton.text().trim()).toBe('Actions');
      });

      it('should have 2 menu items', function () {
        var menuItems = $element.find('li > a');
        expect(menuItems.length).toBe(2);
        expect(menuItems[0].textContent.trim()).toBe('Edit');
        expect(menuItems[1].textContent.trim()).toBe('Delete');
      });

      it('should have one item in list if link clicked', function () {
        $element.find('li > a').first().click();
        expect($scope.testList.length).toBe(1);
        expect($scope.testList[0]).toBe('test');
      });
    });

    describe('split button dropdown', function () {
      var $scope, $element;

      beforeEach(inject(function ($injector) {
        var $compile = $injector.get('$compile');
        var $templateCache = $injector.get('$templateCache');
        var basePath = $injector.get('horizon.framework.widgets.basePath');
        $scope = $injector.get('$rootScope').$new();

        $scope.testList = [];
        $scope.item = 'test';

        $scope.clickMe = function (item) {
          $scope.testList.push(item);
        };

        var markup = $templateCache
          .get(basePath + 'action-list/action-list.split-botton-dropdown.mock.html');

        $element = angular.element(markup);
        $compile($element)($scope);

        $scope.$apply();
      }));

      it('should have one dropdown button', function () {
        var dropdownButton = $element.find('.split-button');
        expect(dropdownButton.length).toBe(1);
        expect(dropdownButton.text().trim()).toBe('View');
      });

      it('should have one caret button', function () {
        expect($element.find('.split-caret').length).toBe(1);
        expect($element.find('.fa-caret-down').length).toBe(1);
      });

      it('should have 2 menu items', function () {
        var menuItems = $element.find('li > a');
        expect(menuItems.length).toBe(2);
        expect(menuItems[0].textContent.trim()).toBe('Edit');
        expect(menuItems[1].textContent.trim()).toBe('Delete');
      });

      it('should have one item in list if "View" clicked', function () {
        $element.find('.split-button').click();
        expect($scope.testList.length).toBe(1);
        expect($scope.testList[0]).toBe('test');
      });

      it('should have 3 items in list if all actions clicked', function () {
        $element.find('.split-button').click();
        $element.find('li > a').click();
        expect($scope.testList.length).toBe(3);
      });
    });

    describe('button group', function () {
      var $scope, $element;

      beforeEach(inject(function ($injector) {
        var $compile = $injector.get('$compile');
        var $templateCache = $injector.get('$templateCache');
        var basePath = $injector.get('horizon.framework.widgets.basePath');
        $scope = $injector.get('$rootScope').$new();

        $scope.testList = [];
        $scope.item = 'test';

        $scope.clickMe = function (item) {
          $scope.testList.push(item);
        };

        var markup = $templateCache
          .get(basePath + 'action-list/button-group.mock.html');

        $element = angular.element(markup);
        $compile($element)($scope);

        $scope.$apply();
      }));

      it('should have 3 buttons in group', function () {
        var buttons = $element.find('button');
        expect(buttons.length).toBe(3);
        expect(buttons[0].textContent.trim()).toBe('View');
        expect(buttons[1].textContent.trim()).toBe('Edit');
        expect(buttons[2].textContent.trim()).toBe('Delete');
      });

      it('should have 3 items in list if all actions clicked', function () {
        $element.find('button').click();
        expect($scope.testList.length).toBe(3);
      });
    });
  });
})();
