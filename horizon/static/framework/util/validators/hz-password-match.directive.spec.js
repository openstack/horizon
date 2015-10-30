/**
 * Copyright 2015 IBM Corp.
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 * http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

(function () {
  'use strict';

  describe('hzPasswordMatch directive', function () {

    var $compile, $rootScope, element, password, cpassword;
    var markup =
      '<form>' +
        '<input type="password" ng-model="user.password" id="password" name="password">' +
        '<input type="password" ng-model="user.cpassword" hz-password-match="password">' +
      '</form>';

    beforeEach(module('horizon.framework.widgets'));
    beforeEach(module('horizon.framework.util.validators'));
    beforeEach(inject(function ($injector) {
      $compile = $injector.get('$compile');
      $rootScope = $injector.get('$rootScope').$new();

      // generate dom from markup
      element = $compile(markup)($rootScope);
      password = element.children('input[name]');
      cpassword = element.children('input[hz-password-match]');

      // setup up initial data
      $rootScope.user = {};
      $rootScope.$apply();
    }));

    it('should be initially empty', function () {
      expect(password.val()).toEqual('');
      expect(password.val()).toEqual(cpassword.val());
      expect(cpassword.hasClass('ng-valid')).toBe(true);
    });

    it('should not match if user changes only password', function () {
      $rootScope.user.password = 'password';
      $rootScope.$apply();
      cpassword.change();
      expect(cpassword.val()).not.toEqual(password.val());
    });

    it('should not match if user changes only confirmation password', function () {
      $rootScope.user.cpassword = 'password';
      $rootScope.$apply();
      cpassword.change();
      expect(cpassword.val()).not.toEqual(password.val());
    });

    it('should match if both passwords are the same', function () {
      $rootScope.user.password = 'password';
      $rootScope.user.cpassword = 'password';
      $rootScope.$apply();
      cpassword.change();
      expect(cpassword.val()).toEqual(password.val());
    });

    it('should not match if both passwords are different', function () {
      $rootScope.user.password = 'password123';
      $rootScope.user.cpassword = 'password345';
      $rootScope.$apply();
      cpassword.change();
      expect(cpassword.val()).not.toEqual(password.val());
    });
  });

})();
