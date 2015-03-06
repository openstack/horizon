/* jshint globalstrict: true */
'use strict';

describe('hz.widget.form module', function(){
  it('should have been defined', function(){
    expect(angular.module('hz.widget.form')).toBeDefined();
  });
});

describe('form directives', function() {
  beforeEach(module('hz'));
  beforeEach(module('hz.widgets'));
  beforeEach(module('hz.widget.form'));

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
}); // end of form directives
