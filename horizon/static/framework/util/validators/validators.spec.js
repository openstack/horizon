(function() {
  'use strict';

  describe('horizon.framework.util.validators module', function() {
    it('should have been defined', function() {
      expect(angular.module('horizon.framework.util.validators')).toBeDefined();
    });
  });

  describe('validators directive', function() {

    beforeEach(module('horizon.framework.widgets'));
    beforeEach(module('horizon.framework.util.validators'));

    describe('validateNumberMax directive', function() {

      var $scope, $form;

      beforeEach(inject(function($injector) {
        var $compile = $injector.get('$compile');
        $scope = $injector.get('$rootScope').$new();

        $scope.count = 0;

        var markup =  '<form name="testForm">' +
                        '<input type="text" name="count" ng-model="count" ' +
                          'validate-number-max="1"/>' +
                      '</form>';

        $compile(angular.element(markup))($scope);
        $form = $scope.testForm;

        $scope.$digest();
      }));

      it('should pass validation initially when count is 0 and max is 1', function() {
        expect($form.count.$valid).toBe(true);
        expect($form.$valid).toBe(true);
      });

      it('should not pass validation if count increased to 2 and max is 1', function() {
        $form.count.$setViewValue(2);
        $scope.$digest();
        expect($form.count.$valid).toBe(false);
        expect($form.$valid).toBe(false);
      });

      it('should pass validation if count is empty', function() {
        $form.count.$setViewValue('');
        $scope.$digest();
        expect($form.count.$valid).toBe(true);
        expect($form.$valid).toBe(true);
      });

    });

    describe('validateNumberMin directive', function() {

      var $scope, $form;

      beforeEach(inject(function($injector) {
        var $compile = $injector.get('$compile');
        $scope = $injector.get('$rootScope').$new();

        $scope.count = 0;

        var markup =  '<form name="testForm">' +
                        '<input type="text" name="count" ng-model="count" ' +
                          'validate-number-min="1"/>' +
                      '</form>';

        $compile(angular.element(markup))($scope);
        $form = $scope.testForm;

        $scope.$digest();
      }));

      it('should not pass validation initially when count is 0 and min is 1', function() {
        expect($form.count.$valid).toBe(false);
        expect($form.$valid).toBe(false);
      });

      it('should pass validation if count increased to 2 and min is 1', function() {
        $form.count.$setViewValue(2);
        $scope.$digest();
        expect($scope.count).toBe(2);
        expect($form.count.$valid).toBe(true);
        expect($form.$valid).toBe(true);
      });

      it('should pass validation if count is empty', function() {
        $form.count.$setViewValue('');
        $scope.$digest();
        expect($form.count.$valid).toBe(true);
        expect($form.$valid).toBe(true);
      });

    });

    describe('hzPasswordMatch directive', function() {

      var $compile, $rootScope;
      var element, password, cpassword;
      var markup =
        '<form name="form">' +
          '<input type="password" ng-model="user.password" name="password">' +
          '<input type="password" ng-model="user.cpassword" ' +
            'hz-password-match="form.password">' +
        '</form>';

      beforeEach(inject(function($injector){
        $compile = $injector.get('$compile');
        $rootScope = $injector.get('$rootScope').$new();

        // generate dom from markup
        element = $compile(markup)($rootScope);
        password = element.children('input[name]');
        cpassword = element.children('input[hz-password-match]');

        // setup up initial data
        $rootScope.user = {};
        $rootScope.$digest();
      }));

      it('should be initially empty', function() {
        expect(password.val()).toEqual('');
        expect(password.val()).toEqual(cpassword.val());
        expect(cpassword.hasClass('ng-valid')).toBe(true);
      });

      it('should not match if user changes only password', function(done) {
        $rootScope.user.password = 'password';
        $rootScope.$digest();
        cpassword.change();
        setTimeout(function(){
          expect(cpassword.val()).not.toEqual(password.val());
          expect(cpassword.hasClass('ng-invalid')).toBe(true);
          done();
        }, 1000);
      });

      it('should not match if user changes only confirmation password', function(done) {
        $rootScope.user.cpassword = 'password';
        $rootScope.$digest();
        cpassword.change();
        setTimeout(function(){
          expect(cpassword.val()).not.toEqual(password.val());
          expect(cpassword.hasClass('ng-invalid')).toBe(true);
          done();
        }, 1000);
      });

      it('should match if both passwords are the same', function(done) {
        $rootScope.user.password = 'password';
        $rootScope.user.cpassword = 'password';
        $rootScope.$digest();
        cpassword.change();
        setTimeout(function(){
          expect(cpassword.val()).toEqual(password.val());
          expect(cpassword.hasClass('ng-valid')).toBe(true);
          done();
        }, 1000);
      });

      it('should not match if both passwords are different', function(done) {
        $rootScope.user.password = 'password123';
        $rootScope.user.cpassword = 'password345';
        $rootScope.$digest();
        cpassword.change();
        setTimeout(function(){
          expect(cpassword.val()).not.toEqual(password.val());
          expect(cpassword.hasClass('ng-invalid')).toBe(true);
          done();
        }, 1000);
      });

    }); // end of hzPasswordMatch directive

  });

})();