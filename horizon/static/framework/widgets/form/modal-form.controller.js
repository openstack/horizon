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
   * @name horizon.framework.widgets.form.ModalFormController
   *
   * @param(object) modal instance from angular-bootstrap
   * @param(object) context object provided by the user
   *
   * @description
   * Controller for a schema-form based modal.
   * If user presses cancel button or closes dialog, modal gets dismissed.
   * If user presses submit button, form input is validated then the modal
   * is closed and the context object is passed back so that the caller can
   * use any of the inputs.
   */
  angular
    .module('horizon.framework.widgets.form')
    .controller('horizon.framework.widgets.form.ModalFormController', controller);

  controller.$inject = [
    '$uibModalInstance',
    'context'
  ];

  function controller($uibModalInstance, context) {
    var ctrl = this;
    ctrl.formTitle = context.schema.title || context.title;
    ctrl.form = context.form;
    ctrl.schema = context.schema;
    ctrl.model = context.model;
    ctrl.submit = submit;
    ctrl.submitText = context.submitText;
    ctrl.submitIcon = context.submitIcon;
    ctrl.cancel = cancel;
    ctrl.helpUrl = context.helpUrl;

    function submit($event, schemaForm) {
      $event.preventDefault();
      $event.stopPropagation();
      if (!schemaForm.$invalid) {
        return $uibModalInstance.close(context);
      }
    }

    function cancel() {
      return $uibModalInstance.dismiss(context);
    }

    return ctrl;
  }
})();
