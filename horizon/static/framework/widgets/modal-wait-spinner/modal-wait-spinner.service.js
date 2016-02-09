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

  WaitSpinnerService.$inject = [
    '$interpolate',
    '$templateCache',
    'horizon.framework.widgets.basePath',
    '$uibModal'
  ];

  /*
   * @ngdoc factory
   * @name horizon.framework.widgets.modal-wait-spinner.factory:WaitSpinnerService
   * @description
   * In order to provide a seamless transition to a Horizon that uses more Angular
   * based pages, the service is currently implemented using the same markup as the
   * client side loader, which is composed of HTML and a spinner Icon Font.
   */

  function WaitSpinnerService ($interpolate, $templateCache, basePath, $uibModal) {
    var spinner = this;
    var service = {
      showModalSpinner: showModalSpinner,
      hideModalSpinner: hideModalSpinner
    };

    return service;

    ////////////////////

    function showModalSpinner(spinnerText) {
      var templateUrl = basePath + 'modal-wait-spinner/modal-wait-spinner.template.html';
      var html = $templateCache.get(templateUrl);
      var modalOptions = {
        backdrop: 'static',
        template: $interpolate(html)({text: spinnerText}),
        windowClass: 'modal-wait-spinner'
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
