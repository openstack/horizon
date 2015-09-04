/*
 * Copyright 2015, Intel Corp.
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

  describe('horizon.framework.widgets.metadata.tree module', function () {
    it('should have been defined', function () {
      expect(angular.module('horizon.framework.widgets.metadata.tree')).toBeDefined();
    });

    var namespaces = [
      {
        "display_name": "Test Namespace A",
        "description": "Test namespace description",
        "properties": {
          "test:A:1": {
            "title": "Test A.1 - string",
            "type": "string",
            "default": "foo",
            "enum": [
              "option-1", "option-2", "option-3"
            ]
          },
          "test:A:2": {
            "title": "Test A.2 - integer",
            "type": "integer",
            "default": "1",
            "minimum": 0,
            "maximum": 10
          },
          "test:A:3": {
            "title": "Test A.3 - number",
            "type": "number",
            "default": "1.1",
            "minimum": 0,
            "maximum": 10
          },
          "test:A:4": {
            "title": "Test A.4 - boolean",
            "type": "boolean",
            "default": "True"
          },
          "test:A:5": {
            "title": "Test A.5 - boolean",
            "type": "boolean",
            "default": "false"
          },
          "test:A:6": {
            "title": "Test A.6 - array",
            "type": "array",
            "items": {
              "type": "string",
              "enum": [
                "val-1", "val-2", "val-3", "val-4"
              ]
            },
            "default": "<in> val-2,val-3"
          }
        }
      },
      {
        "display_name": "Test Namespace B",
        "description": "Test namespace description",
        "objects": [
          {
            "name": "Test Object A",
            "description": "Test object description",
            "properties": {
              "test:B:A:1": {
                "title": "Test B.A.1",
                "description": "Test description"
              },
              "test:B:A:2": {}
            }
          },
          {
            "name": "Test Object B",
            "description": "Test object description",
            "properties": {
              "test:B:B:1": {},
              "test:B:B:2": {}
            }
          }
        ]
      }
    ];

    describe('directives', function () {
      var $scope, $element;

      beforeEach(module('templates'));
      beforeEach(module('horizon.framework'));

      describe('metadataTree directive', function () {

        beforeEach(inject(function ($injector) {
          var $compile = $injector.get('$compile');
          $scope = $injector.get('$rootScope').$new();

          $scope.available = namespaces;
          $scope.existing = { 'test:B:A:1':'foo' };

          var markup = '<metadata-tree' +
                       '  available="available"' +
                       '  existing="existing">' +
                       '</metadata-tree>';

          $element = angular.element(markup);
          $compile($element)($scope);
          $scope.$apply();
        }));

        it('should have 2 rows in available list', function () {
          expect($element.find('ul.list-group:first li[ng-repeat]').length).toBe(2);
        });

        it('should have 1 row in existing list', function () {
          expect($element.find('ul.list-group:last li[ng-repeat]').length).toBe(1);
          var row = $element.find('ul.list-group:last li[ng-repeat]:first');
          expect(row.scope().item.leaf.name).toBe('test:B:A:1');
          expect(row.scope().item.leaf.value).toBe('foo');
        });

        it('should have 10 rows in available list when expanded items', function () {
          $element.find('ul.list-group:first li[ng-repeat]:first').trigger('click');
          $element.find('ul.list-group:first li[ng-repeat]:last').trigger('click');
          expect($element.find('ul.list-group:first li[ng-repeat]').length).toBe(10);
        });

        it('should remove item from available and add it in existing list when added',
          function () {
            $element.find('ul.list-group:first li[ng-repeat]:last') .trigger('click');
            $element.find('ul.list-group:first li[ng-repeat]:last').trigger('click');
            expect($element.find('ul.list-group:first li[ng-repeat]').length).toBe(6);

            $element.find('ul.list-group:first li[ng-repeat]:last .btn').trigger('click');
            expect($element.find('ul.list-group:first li[ng-repeat]').length).toBe(5);
            expect($element.find('ul.list-group:last li[ng-repeat]').length).toBe(2);
            var lastActive = $element.find('ul.list-group:last li[ng-repeat].active');
            expect(lastActive.scope().item.leaf.name).toBe('test:B:B:2');
          }
        );

        it('should add item to available and remove it from existing list when removed',
          function () {
            $element.find('ul.list-group:last li[ng-repeat]:first .btn').trigger('click');
            expect($element.find('ul.list-group:first li[ng-repeat]').length).toBe(6);
            expect($element.find('ul.list-group:last li[ng-repeat]').length).toBe(0);
            var lastActive = $element.find('ul.list-group:first li[ng-repeat].active');
            expect(lastActive.scope().item.leaf.name).toBe('test:B:A:1');
          }
        );

        it('should add custom item to existing list', function () {
          $element.find('ul.list-group:first li:first input').val('custom').trigger('input');
          $element.find('ul.list-group:first li:first .btn').trigger('click');

          expect($element.find('ul.list-group:last li[ng-repeat]').length).toBe(2);
          var lastActive = $element.find('ul.list-group:last li[ng-repeat].active');
          expect(lastActive.scope().item.leaf.name).toBe('custom');
        });
      });

      describe('metadataTreeItem directive', function () {
        var $scope, $element, item;

        beforeEach(inject(function ($injector) {
          var $compile = $injector.get('$compile');
          $scope = $injector.get('$rootScope').$new();

          var serviceName = 'horizon.framework.widgets.metadata.tree.service';
          item = new ($injector.get(serviceName).Item)();
          $scope.item = item.fromProperty('test', namespaces[0].properties['test:A:6']);

          var markup = '<metadata-tree-item' +
                       '  item="item" text="text" action="">' +
                       '</metadata-tree-item>';

          $element = angular.element(markup);
          $compile($element)($scope);
          $scope.$apply();
        }));

        it('should have additional methods for array ', function () {
          expect($element.isolateScope().ctrl.opened).toBe(false);
          expect($element.isolateScope().ctrl.addValue).toBeDefined();
          expect($element.isolateScope().ctrl.removeValue).toBeDefined();
          expect($element.isolateScope().ctrl.switchOpened).toBeDefined();
        });

        it('should add values to array ', function () {
          $element.find('.options li:last').trigger('click');
          expect(item.leaf.getValue()).toBe('<in> val-2,val-3,val-4');
          $element.find('.options li:first').trigger('click');
          expect(item.leaf.getValue()).toBe('<in> val-1,val-2,val-3,val-4');
        });

        it('should remove value from array ', function () {
          $element.find('.values .label:first').trigger('click');
          expect(item.leaf.getValue()).toBe('<in> val-3');
        });
      });
    });
  });

})();
