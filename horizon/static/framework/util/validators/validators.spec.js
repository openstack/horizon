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

  });
})();
