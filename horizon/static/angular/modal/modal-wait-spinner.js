/*
 *    (c) Copyright 2015 Hewlett-Packard Development Company, L.P.
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *    http://www.apache.org/licenses/LICENSE-2.0
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
 @ngdoc overview
 @name hz.widget.modal-wait-spinner
 @description
 A "global" wait spinner that displays a line of text followed by "...".

 Requires {@link http://angular-ui.github.io/bootstrap/ `Angular-bootstrap`}

 Used when the user must wait before any additional action is possible. Can be launched from modal dialogs.

 @example
 <example>
   <pre>
    .controller('MyController', [
      '$scope',
      'modalWaitSpinnerService',
      function (modalWaitSpinnerService) {
        $scope.showSpinner = function () {
          modalWaitSpinnerService.showModalSpinner(gettext("Loading"));
        }
        $scope.hideSpinner = function () {
          modalWaitSpinnerService.hideModalSpinner();
         }
      }
    ])
   </pre>
 </example>

 In order to provide a seamless transition to a Horizon that uses more Angular
 based pages, the service is currently implemented using the existing
 Spin.js library and the corresponding JQuery plugin (jquery.spin.js). This widget looks and feels
 the same as the existing spinner we are familiar with in Horizon. Over time, uses of the existing
 Horizon spinner ( horizon.modals.modal_spinner() ) can be phased out, or refactored to use this
 component.
 */

  angular.module('hz.widget.modal-wait-spinner', [
    'ui.bootstrap',
  ])
    .factory('modalWaitSpinnerService', [
      '$modal',
      function ($modal) {
        var modalInstance;

        var service = {
          showModalSpinner: function (spinnerText) {
            var modalOptions = {
              backdrop:    'static',
              /*
               Using <div> for wait-spinner instead of a wait-spinner element
               because the existing Horizon spinner CSS styling expects a div
               for the modal-body
               */
              template:    '<div wait-spinner class="modal-body" text="' + spinnerText + '"></div>',
              windowClass: 'modal-wait-spinner modal_wrapper loading'
            };
            this.modalInstance = $modal.open(modalOptions);
          },

          hideModalSpinner: function () {
            if (this.modalInstance) {
              this.modalInstance.dismiss();
              delete(this.modalInstance);
            }
          }
        };

        return service;
      }
    ])

    .directive('waitSpinner', function () {

      return {
        scope:    {
          text: '@text'   // One-direction binding (reads from parent)
        },
        restrict: 'A',
        link:     link,
        template: '<p><i>{$text$}&hellip;</i></p>'
      };

      function link($scope, element, attrs) {
        element.spin(horizon.conf.spinner_options.modal);
        /*
         At the time link is executed, element may not have been sized by the browser.
         Spin.js may mistakenly places the spinner at 50% of 0 (left:0, top:0). To work around
         this, explicitly set 50% left and top to center the spinner in the parent
         container
         */
        element.find('.spinner').css({'left': '50%', 'top': '50%'});
      }
    });
})();
