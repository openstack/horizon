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

  /*
   * @ngdoc directive
   * @name horizon.framework.widgets.modal-wait-spinner.directive:waitSpinner
   * @description
   * A "global" wait spinner that displays a line of text followed by "...".
   *
   * Requires {@link http://angular-ui.github.io/bootstrap/ `Angular-bootstrap`}
   *
   * Used when the user must wait before any additional action is possible.  Can be
   * launched from modal dialogs.
   *
   * @example
   * <example>
   *   <pre>
   *    angular
   *      .controller('MyController', MyController);
   *
   *    MyController.$inject = [
   *      '$scope',
   *      'horizon.framework.widgets.modal-wait-spinner.service'
   *    ];
   *
   *    function MyController($scope, modalWaitSpinnerService) {
   *      $scope.showSpinner = function () {
   *        modalWaitSpinnerService.showModalSpinner(gettext("Loading"));
   *      }
   *
   *      $scope.hideSpinner = function () {
   *        modalWaitSpinnerService.hideModalSpinner();
   *      }
   *    }
   *   </pre>
   * </example>
   */

  angular
    .module('horizon.framework.widgets.modal-wait-spinner')
    .directive('waitSpinner', waitSpinner);

  waitSpinner.$inject = ['horizon.framework.widgets.basePath'];

  function waitSpinner(basePath) {

    var directive = {
      scope: {
        text: '@text'   // One-direction binding (reads from parent)
      },
      templateUrl: basePath + 'modal-wait-spinner/modal-wait-spinner.template.html',
      restrict: 'A'
    };

    return directive;
  }
})();
