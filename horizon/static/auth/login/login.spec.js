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

(function() {
  'use strict';

  describe('hzLoginFinder', function() {

    var $compile, $rootScope, $timeout, webssoMarkup, regularMarkup;

    beforeEach(module('templates'));
    beforeEach(module('horizon.auth.login'));
    beforeEach(inject(function(_$compile_, _$rootScope_, _$timeout_, $injector) {
      $compile = _$compile_;
      $rootScope = _$rootScope_;
      $timeout = _$timeout_;
      var $templateCache = $injector.get('$templateCache');
      var basePath = $injector.get('horizon.auth.login.basePath');

      webssoMarkup = $templateCache.get(basePath + 'login.websso.mock.html');
      regularMarkup = $templateCache.get(basePath + 'login.regular.mock.html');

      jasmine.addMatchers({
        // jquery show is not consistent across different browsers
        // on FF, it is 'block' while on chrome it is 'inline'
        // to reconcile this difference, we need a custom matcher
        toBeVisible: function() {
          return {
            compare: function(actual) {
              var pass = (actual.css('display') !== 'none');
              var result = {
                pass: pass,
                message: pass ?
                  'Expected element to be visible' :
                  'Expected element to be visible, but it is hidden'
              };
              return result;
            }
          };
        }
      });
    }));

    describe('when websso is not enabled', function() {
      var element,
        helpText, authType,
        userInput, passwordInput;

      beforeEach(function() {
        element = $compile(regularMarkup)($rootScope);
        authType = element.find('#id_auth_type');
        userInput = element.find("#id_username").parents('.form-group');
        passwordInput = element.find("#id_password").parents('.form-group');
        helpText = element.find('#help_text');
        $rootScope.$apply();
      });

      it('should not contain auth_type select input', function() {
        expect(authType.length).toEqual(0);
      });

      it('should hide help text', function() {
        expect(helpText).not.toBeVisible();
      });

      it('should show username and password inputs', function() {
        expect(userInput).toBeVisible();
        expect(passwordInput).toBeVisible();
      });
    });

    describe('when websso is enabled', function() {

      var element,
        helpText, authType,
        userInput, passwordInput,
        domainInput, regionInput;

      beforeEach(function() {
        element = $compile(webssoMarkup)($rootScope);
        authType = element.find('#id_auth_type');
        userInput = element.find("#id_username").parents('.form-group');
        passwordInput = element.find("#id_password").parents('.form-group');
        domainInput = element.find("#id_domain").parents('.form-group');
        regionInput = element.find("#id_region").parents('.form-group');
        helpText = element.find('#help_text');
        $rootScope.$apply();
      });

      it('should contain auth_type select input', function() {
        expect(authType.length).toEqual(1);
      });

      it('should show help text below auth_type', function() {
        expect(authType.next().get(0)).toEqual(helpText.get(0));
      });

      it('should show help text', function() {
        expect(helpText).toBeVisible();
      });

      it('should show username and password inputs', function() {
        expect(userInput).toBeVisible();
        expect(passwordInput).toBeVisible();
      });

      it('should hide username and password when authentication type is oidc', function() {
        authType.val('oidc');
        authType.change();
        $timeout.flush();
        expect(userInput).not.toBeVisible();
        expect(passwordInput).not.toBeVisible();
      });

      it('should show input fields when authentication type is credentials', function() {
        authType.val('credentials');
        authType.change();
        $timeout.flush();
        expect(userInput).toBeVisible();
        expect(passwordInput).toBeVisible();
        expect(domainInput).toBeVisible();
        expect(regionInput).toBeVisible();
      });
    });
  });
})();
