/**
 * (c) Copyright 2016 Hewlett Packard Enterprise Development Company LP
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

(function() {
  'use strict';

  /**
   * @ngdoc controller
   * @name FormModalController
   *
   * @param(object) modal instance from angular-bootstrap
   * @param(object) context object provided by the user
   *
   * @description
   * Horizon's controller for modal dialog.
   * Passes context along to the template.
   * If user presses cancel button or closes dialog, modal gets dismissed.
   * If user presses submit button, modal gets closed.
   * This controller is automatically included in modalService.
   */
  angular
    .module('horizon.app.core.instances')
    .controller('horizon.app.core.instances.actions.FormModalController', FormModalController);

  FormModalController.$inject = [
    '$modalInstance',
    'context'
  ];

  function FormModalController($modalInstance, context) {
    var ctrl = this;
    ctrl.context = context;
    ctrl.submit = function(form) {
      if ( form.$valid ) {
        $modalInstance.close(context);
      }
    };
    ctrl.cancel = function() {
      $modalInstance.dismiss('cancel');
    };
  } // end of function

})();
