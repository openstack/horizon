(function() {
  'use strict';

  describe('hz.widget.action-list module', function() {
    it('should have been defined', function() {
      expect(angular.module('hz.widget.action-list')).toBeDefined();
    });
  });

  describe('action-list directive', function() {

    beforeEach(module('templates'));
    beforeEach(module('hz'));
    beforeEach(module('hz.widgets'));
    beforeEach(module('hz.widget.action-list'));

    describe('single button dropdown', function() {

      var $scope, $element;

      beforeEach(inject(function($injector) {
        var $compile = $injector.get('$compile');
        $scope = $injector.get('$rootScope').$new();

        $scope.testList = [];

        $scope.clickMe = function(item) {
          $scope.testList.push(item);
        };

        $scope.item = 'test';

        var markup = 
          '<action-list dropdown>' +
          '  <action button-type="single-button">Actions</action>' +
          '  <menu>' +
          '    <action button-type="menu-item" callback="clickMe" item="item">' +
          '      Edit' +
          '    </action>' +
          '    <action button-type="menu-item" callback="clickMe" item="item">' +
          '      Delete' +
          '    </action>' +
          '  </menu>' +
          '</action-list>';

        $element = angular.element(markup);
        $compile($element)($scope);

        $scope.$digest();
      }));

      it('should have one dropdown button', function() {
        var dropdownButton = $element.find('.single-button');
        expect(dropdownButton.length).toBe(1);
        expect(dropdownButton.text().trim()).toBe('Actions');
      });

      it('should have 2 menu items', function() {
        var menuItems = $element.find('li > a');
        expect(menuItems.length).toBe(2);
        expect(menuItems[0].textContent.trim()).toBe('Edit');
        expect(menuItems[1].textContent.trim()).toBe('Delete');
      });

      it('should have one item in list if link clicked', function() {
        $element.find('li > a').first().click();
        expect($scope.testList.length).toBe(1);
        expect($scope.testList[0]).toBe('test');
      });

    });

    describe('split button dropdown', function() {

      var $scope, $element;

      beforeEach(inject(function($injector) {
        var $compile = $injector.get('$compile');
        $scope = $injector.get('$rootScope').$new();

        $scope.testList = [];

        $scope.clickMe = function(item) {
          $scope.testList.push(item);
        };

        $scope.item = 'test';

        var markup =
          '<action-list dropdown>' +
          '  <action button-type="split-button" callback="clickMe" item="item">' +
          '    View' +
          '  </action>' +
          '  <menu>' +
          '    <action button-type="menu-item" callback="clickMe" item="item">' +
          '      Edit' +
          '    </action>' +
          '    <action button-type="menu-item" callback="clickMe" item="item">' +
          '      Delete' +
          '    </action>' +
          '  </menu>' +
          '</action-list>';

        $element = angular.element(markup);
        $compile($element)($scope);

        $scope.$digest();
      }));

      it('should have one dropdown button', function() {
        var dropdownButton = $element.find('.split-button');
        expect(dropdownButton.length).toBe(1);
        expect(dropdownButton.text().trim()).toBe('View');
      });

      it('should have one caret button', function() {
        expect($element.find('.split-caret').length).toBe(1);
        expect($element.find('.caret').length).toBe(1);
      });

      it('should have 2 menu items', function() {
        var menuItems = $element.find('li > a');
        expect(menuItems.length).toBe(2);
        expect(menuItems[0].textContent.trim()).toBe('Edit');
        expect(menuItems[1].textContent.trim()).toBe('Delete');
      });

      it('should have one item in list if "View" clicked', function() {
        $element.find('.split-button').click();
        expect($scope.testList.length).toBe(1);
        expect($scope.testList[0]).toBe('test');
      });

      it('should have 3 items in list if all actions clicked', function() {
        $element.find('.split-button').click();
        $element.find('li > a').click();
        expect($scope.testList.length).toBe(3);
      });

    });

    describe('button group', function() {

      var $scope, $element;

      beforeEach(inject(function($injector) {
        var $compile = $injector.get('$compile');
        $scope = $injector.get('$rootScope').$new();

        $scope.testList = [];

        $scope.clickMe = function(item) {
          $scope.testList.push(item);
        };

        $scope.item = 'test';

        var markup = '<action-list dropdown>' +
          ' <action callback="clickMe" item="item">View</action>' +
          ' <action callback="clickMe" item="item">Edit</action>' +
          ' <action callback="clickMe" item="item">Delete</action>' +
          '</action-list>';

        $element = angular.element(markup);
        $compile($element)($scope);

        $scope.$digest();
      }));

      it('should have 3 buttons in group', function() {
        var buttons = $element.find('button');
        expect(buttons.length).toBe(3);
        expect(buttons[0].textContent.trim()).toBe('View');
        expect(buttons[1].textContent.trim()).toBe('Edit');
        expect(buttons[2].textContent.trim()).toBe('Delete');
      });

      it('should have 3 items in list if all actions clicked', function() {
        $element.find('button').click();
        expect($scope.testList.length).toBe(3);
      });

    });

  });

})();