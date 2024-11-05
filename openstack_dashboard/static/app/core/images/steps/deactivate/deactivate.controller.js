(function () {

  'use strict';

  angular
    .module('horizon.app.core.images')
    .controller('horizon.app.core.images.steps.DeactivateController', DeactivateController);

  DeactivateController.$inject = [
    '$scope'
  ];

  function DeactivateController(
    $scope
  ) {
    var ctrl = this;

    ctrl.imageStatusOptions = [
          { label: gettext('Active'), value: 'active' },
          { label: gettext('Deactivated'), value: 'deactivated' }
    ];

    ctrl.onStatusChange = onStatusChange;

    $scope.imagePromise.then(init);

      ///////////////////////////

    ctrl.toggleDeactivate = function () {
      ctrl.image.status = ctrl.image.status === 'active' ? 'deactivated' : 'active';
      $scope.stepModels.deactivateForm.deactivate = ctrl.image.status === 'deactivated';
    };

    function init(response) {
      $scope.stepModels.deactivateForm = $scope.stepModels.deactivateForm || {};
      ctrl.image = response.data;
      ctrl.image.status = ctrl.image.status || 'active'; // initial status
      updateDeactivateFlag();
    }

    function onStatusChange () {
      updateDeactivateFlag();
    }

    function updateDeactivateFlag () {
      $scope.stepModels.deactivateForm.deactivate = ctrl.image.status === 'deactivated';
    }
  }
})();
// end of controller
