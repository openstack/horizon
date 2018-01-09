/**
 * (c) Copyright 2015 Hewlett-Packard Development Company, L.P.
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

  /**
   * @ngdoc directive
   * @name hzPasswordMatch
   * @element ng-model
   *
   * @description
   * A directive to ensure that password matches.
   * Changing the password or confirmation password triggers a validation check.
   * The goal is to check that confirmation password matches the password.
   *
   * @restrict A
   *
   * @scope
   * hzPasswordMatch - model value to validate against
   *
   * @example:
   * <form name="form">
   *  <input type='password' id="psw" ng-model="user.psw" name="psw">
   *  <input type='password' ng-model="user.cnf" hz-password-match="user.psw">
   * </form>
   */
  angular
    .module('horizon.framework.util.validators')
    .directive('hzPasswordMatch', hzPasswordMatch);

  function hzPasswordMatch() {
    return {
      restrict: 'A',
      require: 'ngModel',
      link: link
    };

    ///////////

    function link(scope, element, attr, ngModelCtrl) {
      /**
       * this ensures that typing in either input
       * will trigger the password match
       */
      scope.$watch(attr.hzPasswordMatch, function(value) {
        scope.passwordConfirm = value;
        ngModelCtrl.$validate();
      });

      // helper function to check that password matches
      ngModelCtrl.$validators.check = function (modelValue, viewValue) {
        var value = modelValue || viewValue;
        return value === scope.passwordConfirm;
      };
    } // end of link
  } // end of directive
})();
