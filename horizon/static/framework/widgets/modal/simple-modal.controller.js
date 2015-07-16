(function() {
  'use strict';

  /**
   * @ngdoc controller
   * @name SimpleModalController
   *
   * @param(object) scope of the controller
   * @param(object) modal instance from angular-bootstrap
   * @param(object) context object provided by the user
   *
   * @description
   * Horizon's controller for confirmation dialog.
   * Passes context along to the template.
   * If user presses cancel button or closes dialog, modal gets dismissed.
   * If user presses submit button, modal gets closed.
   * This controller is automatically included in modalService.
   */
  angular
    .module('horizon.framework.widgets.modal')
    .controller('SimpleModalController', SimpleModalController);

  SimpleModalController.$inject = [
    '$modalInstance',
    'context'
  ];

  function SimpleModalController($modalInstance, context) {
    var ctrl = this;
    ctrl.context = context;
    ctrl.submit = function() { $modalInstance.close(); };
    ctrl.cancel = function() { $modalInstance.dismiss('cancel'); };
  } // end of function

})();
