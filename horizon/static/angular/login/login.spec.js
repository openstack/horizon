/**
 * Copyright 2015 IBM Corp.
 *
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

/* jshint globalstrict: true */
'use strict';

describe('hzLoginCtrl', function(){

  var $controller;

  beforeEach(module('hz'));
  beforeEach(inject(function(_$controller_){
    $controller = _$controller_;
  }));

  describe('$scope.auth_type', function(){
    it('should initialize to credentials', function(){
      var scope = {};
      var controller = $controller('hzLoginCtrl', { $scope: scope });
      expect(scope.auth_type).toEqual('credentials');
    });
  });

});

describe('hzLoginFinder', function(){

  var $compile, $rootScope, $timeout;

  var websso_markup =
  '<form>' +
    '<p id="help_text">Some help text.</p>' +
    '<fieldset hz-login-finder>' +
      '<div>' +
        '<select id="id_auth_type">' +
          '<option value="credentials">Credentials</option>' +
          '<option value="oidc">OpenID Connect</option>' +
        '</select>' +
      '</div>' +
      '<div class="form-group"><input id="id_username"></div>' +
      '<div class="form-group"><input id="id_password"></div>' +
    '</fieldset>' +
  '</form>';

  var regular_markup =
  '<form>' +
    '<p id="help_text">Some help text.</p>' +
    '<fieldset hz-login-finder>' +
      '<div class="form-group"><input id="id_username"></div>' +
      '<div class="form-group"><input id="id_password"></div>' +
    '</fieldset>' +
  '</form>';

  beforeEach(module('hz'));
  beforeEach(inject(function(_$compile_, _$rootScope_, _$timeout_){
    $compile = _$compile_;
    $rootScope = _$rootScope_;
    $timeout = _$timeout_;

    jasmine.addMatchers({
      // jquery show is not consistent across different browsers
      // on FF, it is 'block' while on chrome it is 'inline'
      // to reconcile this difference, we need a custom matcher
      toBeVisible: function(){
        return {
          compare: function(actual){
            var pass = (actual.css('display') !== 'none');
            var result = {
              pass: pass,
              message: pass?
                'Expected element to be visible':
                'Expected element to be visible, but it is hidden'
            };
            return result;
          }
        };
      }
    });
  }));

  describe('when websso is not enabled', function(){

    var element,
    helpText, authType,
    userInput, passwordInput;

    beforeEach(function(){
      element = $compile(regular_markup)($rootScope);
      authType = element.find('#id_auth_type');
      userInput = element.find("#id_username").parents('.form-group');
      passwordInput = element.find("#id_password").parents('.form-group');
      helpText = element.find('#help_text');
      $rootScope.$digest();
    });

    it('should not contain auth_type select input', function(){
      expect(authType.length).toEqual(0);
    });

    it('should hide help text', function(){
      expect(helpText).not.toBeVisible();
    });

    it('should show username and password inputs', function(){
      expect(userInput).toBeVisible();
      expect(passwordInput).toBeVisible();
    });

  });

  describe('when websso is enabled', function(){

    var element,
    helpText, authType,
    userInput, passwordInput;

    beforeEach(function(){
      element = $compile(websso_markup)($rootScope);
      authType = element.find('#id_auth_type');
      userInput = element.find("#id_username").parents('.form-group');
      passwordInput = element.find("#id_password").parents('.form-group');
      helpText = element.find('#help_text');
      $rootScope.$digest();
    });

    it('should contain auth_type select input', function(){
      expect(authType.length).toEqual(1);
    });

    it('should show help text below auth_type', function(){
      expect(authType.next().get(0)).toEqual(helpText.get(0));
    });

    it('should show help text', function(){
      expect(helpText).toBeVisible();
    });

    it('should show username and password inputs', function(){
      expect(userInput).toBeVisible();
      expect(passwordInput).toBeVisible();
    });

    it('should hide username and password when user picks oidc', function(){
      authType.val('oidc');
      authType.change();
      $timeout.flush();
      expect(userInput).not.toBeVisible();
      expect(passwordInput).not.toBeVisible();
    });

  });

});