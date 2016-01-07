/*
 * Licensed under the Apache License, Version 2.0 (the 'License');
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *    http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an 'AS IS' BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */
(function () {
  'use strict';

  angular
    .module('horizon.app')
    .controller('RedirectController', RedirectController);

  RedirectController.$inject = [
    '$window',
    '$location',
    'horizon.framework.util.i18n.gettext',
    'horizon.framework.widgets.modal-wait-spinner.service'
  ];

  /**
   * @ngdoc controller
   * @name RedirectController
   *
   * @description
   * Controller to redirect to current location.
   * It forces a reload from the server when the clicked link doesn't match
   * an current Angular route configured in the $routeProvider Service.
   *
   * This controller is used in the 'otherwise' of the $routeProvider Service.
   * It gives the Django code a chance to try and find a matching template for the requested URL.
   */
  function RedirectController(
    $window,
    $location,
    gettext,
    waitSpinnerService
  ) {
    waitSpinnerService.showModalSpinner(gettext('Loading'));
    $window.location.href = $location.path();
  }

}());
