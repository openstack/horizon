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

  waitSpinner.$inject = ['horizon.framework.conf.spinner_options'];

  function waitSpinner(spinnerOptions) {

    var directive = {
      scope: {
        text: '@text'   // One-direction binding (reads from parent)
      },
      restrict: 'A',
      link:     link,
      template: '<p><i>{$text$}&hellip;</i></p>'
    };

    return directive;

    ////////////////////

    /*
     * At the time link is executed, element may not have been sized by the browser.
     * Spin.js may mistakenly places the spinner at 50% of 0 (left:0, top:0). To work around
     * this, explicitly set 50% left and top to center the spinner in the parent
     * container
     */
    function link(scope, element) {
      element.spin(spinnerOptions.modal);
      element.find('.spinner').css({'left': '50%', 'top': '50%'});
    }
  }
})();
