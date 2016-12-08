/**
 * Licensed under the Apache License, Version 2.0 (the "License"); you may
 * not use this file except in compliance with the License. You may obtain
 * a copy of the License at
 *
 *    http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
 * WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
 * License for the specific language governing permissions and limitations
 * under the License.
 */

(function () {
  'use strict';

  describe('horizon.framework.util.bind-scope module', function () {
    it('should have been defined', function () {
      expect(angular.module('horizon.framework.util.bind-scope')).toBeDefined();
    });
  });

  describe('bind-scope directive', function () {
    var $scope, $element;

    beforeEach(module('horizon.framework'));

    beforeEach(module('horizon.framework.util.bind-scope', function ($compileProvider) {
      /* eslint-disable angular/module-getter */
      $compileProvider.directive('testBindScope', testBindScope);
      /* eslint-enable angular/module-getter */

      function testBindScope() {
        var directive = {
          restrict: 'E',
          scope: {
            itemList: '='
          },
          transclude: true,
          template: '<ul><li ng-repeat="item in itemList" bind-scope>' +
                    '  <span bind-scope-target></span>' +
                    '</li></ul>'
        };
        return directive;
      }
    }));

    beforeEach(inject(function ($injector) {
      var $compile = $injector.get('$compile');
      $scope = $injector.get('$rootScope').$new();

      $scope.fakeData = [
        { id: '1', animal: 'cat' },
        { id: '2', animal: 'dog' },
        { id: '3', animal: 'fish' }
      ];

      var markup = '<test-bind-scope item-list="fakeData">{$ item.animal $}</test-bind-scope>';

      $element = angular.element(markup);
      $compile($element)($scope);

      $scope.$apply();
    }));

    it('should have 3 list items', function () {
      expect($element.find('li').length).toBe(3);
    });

    it('should have 3 list items with values "cat", "dog" and "fish"', function () {
      var listItems = $element.find('li');
      expect(listItems[0].textContent.trim()).toBe('cat');
      expect(listItems[1].textContent.trim()).toBe('dog');
      expect(listItems[2].textContent.trim()).toBe('fish');
    });
  });
})();
