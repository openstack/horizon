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

  describe('horizon.framework.widgets.metadata.display module', function () {
    it('should have been defined', function () {
      expect(angular.module('horizon.framework.widgets.metadata.display')).toBeDefined();
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
                "val-1", "val-2", "val-3"
              ]
            }
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

    var existing = {
      'test:A:1': 'option-2',
      'test:A:2': '5',
      'test:B:A:1': 'foo',
      'test:B:B:1': 'bar'
    };

    describe('metadataDisplay directive', function () {
      var $scope, $element;

      beforeEach(module('templates'));
      beforeEach(module('horizon.framework'));
      beforeEach(inject(function ($injector) {
        var $compile = $injector.get('$compile');
        $scope = $injector.get('$rootScope').$new();

        $scope.available = namespaces;
        $scope.existing = existing;

        var markup = '<metadata-display' +
                     '  available="available"' +
                     '  existing="existing">' +
                     '</metadata-display>';

        $element = angular.element(markup);
        $compile($element)($scope);
        $scope.$apply();
      }));

      it('should have 3 rows in selector list', function () {
        expect($element.find('.selector .selector-item').length).toBe(3);
      });

      it('should have 2 items in first group', function () {
        expect($element.find('div[ng-repeat] div.auto-width').length).toBe(2);
      });

      it('should have 1 item in second group', function () {
        $element.find('.selector .selector-item:nth-child(2)').trigger('click');
        expect($element.find('div[ng-repeat] div.auto-width').length).toBe(1);
      });

      it('should have proper description', function () {
        var selector = 'span[ng-bind="ctrl.selected.description"]';
        expect($element.find(selector).text()).toBe(namespaces[0].description);
        $element.find('.selector .selector-item:nth-child(2)').trigger('click');
        expect($element.find(selector).text()).toBe(namespaces[1].objects[0].description);
      });
    });
  });
})();
