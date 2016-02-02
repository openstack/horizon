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

  angular
    .module('horizon.auth.login')
    /**
     * @ngdoc hzLoginFinder
     * @description
     * A directive to show or hide inputs and help text
     * based on which authentication method the user selected.
     * Since HTML is generated server-side via Django form,
     * this directive is the hook to make it more dynamic.
     * Only visible if websso is enabled.
     */
    .directive('hzLoginFinder', hzLoginFinder);

  hzLoginFinder.$inject = ['$timeout'];

  function hzLoginFinder($timeout) {
    return {
      restrict: 'A',
      controller: 'hzLoginController',
      link: function(scope, element, attrs, ctrl) {

        /**
         * Test code does not have access to document,
         * so we are restricted to search through the element
         */
        var authType = element.find('#id_auth_type');
        var userInput = element.find("#id_username").parents('.form-group');
        var passwordInput = element.find("#id_password").parents('.form-group');
        var domainInput = element.find('#id_domain').parents('.form-group');
        var regionInput = element.find('#id_region').parents('.form-group');

        /**
         * `helpText` exists outside of element,
         * so we have to traverse one node up
         */
        var helpText = element.parent().find('.help_text');
        helpText.hide();

        // Update the visuals when user selects item from dropdown
        function onChange() {
          $timeout(function() {

            /**
             * If auth_type is 'credential', show the username and password fields,
             * and domain and region if applicable
             */
            ctrl.auth_type = authType.val();
            switch (ctrl.auth_type) {
              case 'credentials':
                userInput.show();
                passwordInput.show();
                domainInput.show();
                regionInput.show();
                break;
              default:
                userInput.hide();
                passwordInput.hide();
                domainInput.hide();
                regionInput.hide();
            }
          }); // end of timeout
        } // end of onChange

        // If authType field exists then websso was enabled
        if (authType.length > 0) {

          /**
           * Programmatically insert help text after dropdown.
           * This is the only way to do it since template is generated server side,
           * via form_fields
           */
          authType.after(helpText);
          helpText.show();

          // Trigger the onChange on first load so that initial choice is auto-selected
          onChange();
          authType.change(onChange);
        }
      } // end of link
    }; // end of return
  } // end of directive

})();
