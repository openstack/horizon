/**
 *
 * (c) Copyright 2016 Hewlett Packard Enterprise Development Company LP
 *
 * Licensed under the Apache License, Version 2.0 (the "License"); you may
 * not use self file except in compliance with the License. You may obtain
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
    .module('horizon.framework.widgets.form')
    .factory('horizon.framework.widgets.form.ModalFormService', service);

  service.$inject = [
    '$uibModal',
    'horizon.framework.widgets.basePath'
  ];

  /**
   * @ngDoc factory
   * @name horizon.framework.widgets.form.ModalFormService
   *
   * @Description
   * Loads a Schema-Form (see modal-form.html) in a modal and returns the modal result promise.
   */
  function service(
    $uibModal,
    widgetsBasePath
  ) {

    var service = {
      open: open
    };

    return service;

    /////////////////

    function open(config) {
      var modalConfig = {
        backdrop: 'static',
        size: config.size || 'lg',
        resolve: {
          context: function() {
            return {
              title: config.title,
              submitText: config.submitText || gettext("Submit"),
              submitIcon: config.submitIcon || "check",
              schema: config.schema,
              form: config.form,
              model: config.model,
              helpUrl: config.helpUrl
            };
          }
        },
        controller: 'horizon.framework.widgets.form.ModalFormController as ctrl',
        templateUrl: widgetsBasePath + 'form/modal-form.html'
      };

      return $uibModal.open(modalConfig).result;
    }
  }
})();
