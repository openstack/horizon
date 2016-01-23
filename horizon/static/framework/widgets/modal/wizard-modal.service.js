/**
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
   * @ngdoc service
   * @name horizon.framework.widgets.modal.wizard-modal.service
   *
   * @description
   * Horizon's wrapper for angular-bootstrap modal service.
   * It should only be use for Wizard dialogs.
   *
   * @example:
   *  angular
   *    .controller('modalExampleCtrl', ExampleCtrl);
   *
   *  ExampleCtrl.$inject = [
   *    '$scope',
   *    'horizon.framework.widgets.modal.wizard-modal.service'
   *  ];
   *
   *  function ExampleCtrl($scope, wizardModalService) {
   *    var options = {
   *      scope: scope, // the scope to use for the Wizard
   *      workflow: workflow, // the workflow used in the wizard
   *      submit: submit // callback to call on a wizard submit
   *    };
   *
   *    wizardModalService(options);
   *  });
   */
  angular
    .module('horizon.framework.widgets.modal')
    .factory('horizon.framework.widgets.modal.wizard-modal.service', WizardModalService);

  WizardModalService.$inject = [
    '$modal'
  ];

  function WizardModalService($modal) {
    var service = {
      modal: modal
    };

    return service;

    ////////////////////

    function modal(params) {
      if (params && params.scope && params.workflow && params.submit) {
        var options = {
          controller: 'WizardModalController as modalCtrl',
          scope: params.scope,
          template: '<wizard></wizard>',
          backdrop: 'static',
          windowClass: 'modal-dialog-wizard',
          resolve: {
            workflow: function() {
              return params.workflow;
            },
            submit: function() {
              return params.submit;
            }
          }
        };

        return $modal.open(options);
      }
    }
  }
})();
