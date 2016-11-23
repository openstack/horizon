/**
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

(function () {
  'use strict';

  angular
    .module('horizon.framework.widgets.modal-wait-spinner')
    .factory('horizon.framework.widgets.modal-wait-spinner.service', WaitSpinnerService);

  WaitSpinnerService.$inject = ['$uibModal'];

  /*
   * @ngdoc factory
   * @name horizon.framework.widgets.modal-wait-spinner.factory:WaitSpinnerService
   * @description
   * In order to provide a seamless transition to a Horizon that uses more Angular
   * based pages, the service is currently implemented using the existing
   * Spin.js library and the corresponding jQuery plugin (jquery.spin.js). This widget
   * looks and feels the same as the existing spinner we are familiar with in Horizon.
   * Over time, uses of the existing Horizon spinner ( horizon.modals.modal_spinner() )
   * can be phased out, or refactored to use this component.
   */
  function WaitSpinnerService ($uibModal) {
    var spinner = this;
    var service = {
      showModalSpinner: showModalSpinner,
      hideModalSpinner: hideModalSpinner
    };

    return service;

    ////////////////////

    function showModalSpinner(spinnerText) {
      var modalOptions = {
        backdrop: 'static',
        /*
         * Using <div> for wait-spinner instead of a wait-spinner element
         * because the existing Horizon spinner CSS styling expects a div
         * for the modal-body
         */
        template: '<div wait-spinner class="modal-body" text="' + spinnerText + '"></div>',
        windowClass: 'modal-wait-spinner modal_wrapper loading'
      };
      spinner.modalInstance = $uibModal.open(modalOptions);
    }

    function hideModalSpinner() {
      if (spinner.modalInstance) {
        spinner.modalInstance.dismiss();
        delete spinner.modalInstance;
      }
    }
  }
})();
