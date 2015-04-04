/* jshint globalstrict: true */
'use strict';

describe('hz.widget.metadata-tree module', function() {
  it('should have been defined', function () {
    expect(angular.module('hz.widget.metadata-tree')).toBeDefined();
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
    beforeEach(module('hz'));
    beforeEach(module('hz.widgets'));
    beforeEach(module('hz.widget.metadata-tree'));

    describe('hzMetadataTree directive', function() {
      beforeEach(inject(function ($injector) {
        var $compile = $injector.get('$compile');
        $scope = $injector.get('$rootScope').$new();

        $scope.available = namespaces;
        $scope.existing = {'test:B:A:1':'foo'};

        var markup =
          '<hz-metadata-tree available="available" existing="existing"></hz-metadata-tree>';

        $element = angular.element(markup);
        $compile($element)($scope);
        $scope.$digest();
      }));

      it('should have 2 rows in available list', function() {
        expect($element.find('ul.list-group:first li[ng-repeat]').length).toBe(2);
      });

      it('should have 1 row in existing list', function() {
        expect($element.find('ul.list-group:last li[ng-repeat]').length).toBe(1);
        expect($element.find('ul.list-group:last li[ng-repeat]:first').scope().item.leaf.name).toBe('test:B:A:1');
        expect($element.find('ul.list-group:last li[ng-repeat]:first').scope().item.leaf.value).toBe('foo');
      });

      it('should have 10 rows in available list when expanded items', function() {
        $element.find('ul.list-group:first li[ng-repeat]:first').trigger('click');
        $element.find('ul.list-group:first li[ng-repeat]:last').trigger('click');
        expect($element.find('ul.list-group:first li[ng-repeat]').length).toBe(10);
      });

      it('should remove item from available and add it in existing list when added', function() {
        $element.find('ul.list-group:first li[ng-repeat]:last').trigger('click');
        $element.find('ul.list-group:first li[ng-repeat]:last').trigger('click');
        expect($element.find('ul.list-group:first li[ng-repeat]').length).toBe(6);
        $element.find('ul.list-group:first li[ng-repeat]:last .btn').trigger('click');
        expect($element.find('ul.list-group:first li[ng-repeat]').length).toBe(5);
        expect($element.find('ul.list-group:last li[ng-repeat]').length).toBe(2);
        expect($element.find('ul.list-group:last li[ng-repeat].active').scope().item.leaf.name).toBe('test:B:B:2');
      });

      it('should add item to available and remove it from existing list when removed', function() {
        $element.find('ul.list-group:last li[ng-repeat]:first .btn').trigger('click');
        expect($element.find('ul.list-group:first li[ng-repeat]').length).toBe(6);
        expect($element.find('ul.list-group:last li[ng-repeat]').length).toBe(0);
        expect($element.find('ul.list-group:first li[ng-repeat].active').scope().item.leaf.name).toBe('test:B:A:1');
      });

      it('should add custom item to existing list', function() {
        $element.find('ul.list-group:first li:first input').val('custom').trigger('input');
        $element.find('ul.list-group:first li:first .btn').trigger('click');
        expect($element.find('ul.list-group:last li[ng-repeat]').length).toBe(2);
        expect($element.find('ul.list-group:last li[ng-repeat].active').scope().item.leaf.name).toBe('custom');
      });
    });

    describe('hzMetadataTreeItem directive', function() {
      var $scope, $element, item;

      beforeEach(inject(function ($injector) {
        var $compile = $injector.get('$compile');
        $scope = $injector.get('$rootScope').$new();

        item = new ($injector.get('metadataTreeService').Item)();
        $scope.item = item.fromProperty('test', namespaces[0].properties['test:A:6']);

        var markup =
        '<hz-metadata-tree-item item="item" text="text" action=""></hz-metadata-tree-item>';

        $element = angular.element(markup);
        $compile($element)($scope);
        $scope.$digest();
      }));

      it('should have additional methods for array ', function () {
        expect($element.isolateScope().opened).toBe(false);
        expect($element.isolateScope().add).toBeDefined();
        expect($element.isolateScope().remove).toBeDefined();
        expect($element.isolateScope().open).toBeDefined();
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
