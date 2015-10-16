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
   * hzPasswordMatch - id of element to validate against
   *
   * @example:
   * <form name="form">
   *  <input type='password' id="psw" ng-model="user.psw" name="psw">
   *  <input type='password' ng-model="user.cnf" hz-password-match="psw">
   * </form>
   *
   * Note that id and name are required for the password input.
   * This directive uses the form model and id for validation check.
   */
  angular
    .module('horizon.framework.util.validators')
    .directive('hzPasswordMatch', hzPasswordMatch);

  function hzPasswordMatch() {
    var directive = {
      restrict: 'A',
      require: 'ngModel',
      link: link
    };

    return directive;

    ///////////

    function link(scope, element, attr, ctrl) {

      /**
       * this ensures that typing in either input
       * will trigger the password match
       */
      var pwElement = angular.element('#' + attr.hzPasswordMatch);
      pwElement.on('keyup change', passwordCheck);
      element.on('keyup change', passwordCheck);

      // helper function to check that password matches
      function passwordCheck() {
        scope.$apply(function () {
          var match = (ctrl.$modelValue === pwElement.val());
          ctrl.$setValidity('match', match);
        });
      }
    } // end of link
  } // end of directive
})();
