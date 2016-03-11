(function () {
  'use strict';

  describe('horizon.framework.util.validators module', function () {
    it('should have been defined', function () {
      expect(angular.module('horizon.framework.util.validators')).toBeDefined();
    });
  });

  describe('validators directive', function () {
    beforeEach(module('horizon.framework'));

    describe('validateNumberMax directive', function () {
      var $scope, $form;

      beforeEach(inject(function ($injector) {
        var $compile = $injector.get('$compile');
        $scope = $injector.get('$rootScope').$new();

        $scope.count = 0;

        var markup = '<form name="testForm">' +
                        '<input type="text" name="count" ng-model="count" ' +
                          'validate-number-max="1"/>' +
                     '</form>';

        $compile(angular.element(markup))($scope);
        $form = $scope.testForm;

        $scope.$apply();
      }));

      it('should pass validation initially when count is 0 and max is 1', function () {
        expect($form.count.$valid).toBe(true);
        expect($form.$valid).toBe(true);
      });

      it('should not pass validation if count increased to 2 and max is 1', function () {
        $form.count.$setViewValue(2);
        $scope.$apply();
        expect($form.count.$valid).toBe(false);
        expect($form.$valid).toBe(false);
      });

      it('should pass validation if count is empty', function () {
        $form.count.$setViewValue('');
        $scope.$apply();
        expect($form.count.$valid).toBe(true);
        expect($form.$valid).toBe(true);
      });
    });

    describe('validateNumberMin directive', function () {
      var $scope, $form;

      beforeEach(inject(function ($injector) {
        var $compile = $injector.get('$compile');
        $scope = $injector.get('$rootScope').$new();

        $scope.count = 0;

        var markup = '<form name="testForm">' +
                        '<input type="text" name="count" ng-model="count" ' +
                          'validate-number-min="1"/>' +
                     '</form>';

        $compile(angular.element(markup))($scope);
        $form = $scope.testForm;

        $scope.$apply();
      }));

      it('should not pass validation initially when count is 0 and min is 1', function () {
        expect($form.count.$valid).toBe(false);
        expect($form.$valid).toBe(false);
      });

      it('should pass validation if count increased to 2 and min is 1', function () {
        $form.count.$setViewValue(2);
        $scope.$apply();
        expect($scope.count).toBe(2);
        expect($form.count.$valid).toBe(true);
        expect($form.$valid).toBe(true);
      });

      it('should pass validation if count is empty', function () {
        $form.count.$setViewValue('');
        $scope.$apply();
        expect($form.count.$valid).toBe(true);
        expect($form.$valid).toBe(true);
      });
    });

    describe('validateUnique directive', function () {

      var scope, port, name, protocol;
      var items = [{ id: '1', protocol: 'HTTP' },
                   { id: '2', protocol: 'HTTPS' },
                   { id: '3', protocol: 'TCP' }];
      var markup =
        '<form>' +
          '<input type="number" id="port" ng-model="port" validate-unique="ports">' +
          '<input id="name" ng-model="name" validate-unique="names">' +
          '<input id="protocol" ng-model="protocol" validate-unique="protocolIsUnique">' +
        '</form>';

      function protocolIsUnique(value) {
        return !items.some(function(item) {
          return item.protocol === value;
        });
      }

      beforeEach(inject(function ($injector) {
        var compile = $injector.get('$compile');
        scope = $injector.get('$rootScope').$new();

        // generate dom from markup
        var element = compile(markup)(scope);
        port = element.children('#port');
        name = element.children('#name');
        protocol = element.children('#protocol');

        // set initial data
        scope.ports = [80, 443];
        scope.names = ['name1', 'name2'];
        scope.protocolIsUnique = protocolIsUnique;
        scope.$apply();
      }));

      it('should be initially empty', function () {
        expect(port.val()).toEqual('');
        expect(name.val()).toEqual('');
        expect(protocol.val()).toEqual('');
        expect(port.hasClass('ng-valid')).toBe(true);
        expect(name.hasClass('ng-valid')).toBe(true);
        expect(protocol.hasClass('ng-valid')).toBe(true);
      });

      it('should be invalid if values are not unique', function () {
        scope.port = 80;
        scope.name = 'name1';
        scope.protocol = 'TCP';
        scope.$apply();
        expect(port.hasClass('ng-valid')).toBe(false);
        expect(name.hasClass('ng-valid')).toBe(false);
        expect(protocol.hasClass('ng-valid')).toBe(false);
      });

      it('should be valid if values are unique', function () {
        scope.port = 81;
        scope.name = 'name3';
        scope.protocol = 'TERMINATED_HTTPS';
        scope.$apply();
        expect(port.hasClass('ng-valid')).toBe(true);
        expect(name.hasClass('ng-valid')).toBe(true);
        expect(protocol.hasClass('ng-valid')).toBe(true);
      });

      it('should be valid if param is undefined', function () {
        delete scope.ports;
        scope.port = 80;
        scope.$apply();
        expect(port.hasClass('ng-valid')).toBe(true);
      });

      it('should be valid if param is a string', function () {
        scope.ports = '80';
        scope.port = 80;
        scope.$apply();
        expect(port.hasClass('ng-valid')).toBe(true);
      });

      it('should be valid if param is a number', function () {
        scope.ports = 80;
        scope.port = 80;
        scope.$apply();
        expect(port.hasClass('ng-valid')).toBe(true);
      });

      it('should be valid if param is an object', function () {
        scope.ports = { port: 80 };
        scope.port = 80;
        scope.$apply();
        expect(port.hasClass('ng-valid')).toBe(true);
      });
    });

  });
})();
