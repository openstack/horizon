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
    .module('horizon.framework.widgets.modal')
    .controller('WizardModalController', WizardModalController);

  WizardModalController.$inject = [
    '$modalInstance',
    '$scope',
    'workflow', // modal injected
    'submit'    // modal injected
  ];

  /**
   * @ngdoc controller
   * @name WizardModalController
   * @module horizon.framework.widgets.modal
   * @description
   * A modal controller for the wizard based workflows.
   * This controller is automatically included in WizardModalService.
   * This controller sets the modal actions and workflow on the given scope
   * as the Wizard needs them defined on the scope.
   */
  function WizardModalController($modalInstance, $scope, workflow, submit) {

    /* eslint-disable angular/controller-as */
    $scope.close = close;
    $scope.cancel = cancel;
    $scope.submit = submit;
    $scope.workflow = workflow;
    /* eslint-enable angular/controller-as */

    function close(args) {
      $modalInstance.close(args);
    }

    function cancel() {
      $modalInstance.dismiss('cancel');
    }
  }

})();
