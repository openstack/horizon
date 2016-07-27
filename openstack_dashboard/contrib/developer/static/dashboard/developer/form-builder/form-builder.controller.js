/*
 * (c) Copyright 2016 Hewlett Packard Enterprise Development Company LP
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *    http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

(function() {
  'use strict';

  angular
    .module('horizon.dashboard.developer.form-builder')
    .controller('horizon.dashboard.developer.form-builder.FormBuilderController', controller);

  controller.$inject = [
    '$http',
    '$scope',
    'horizon.framework.widgets.form.ModalFormService',
    'horizon.dashboard.developer.form-builder.basePath',
    'horizon.framework.util.i18n.gettext',
  ];

  /**
   * @ngdoc controller
   * @name horizon.dashboard.developer.form-builder:FormBuilderController
   * @description
   * This controller allows the launching of any actions registered for resource types
   */
  function controller($http, $scope, modalFormService, basePath, gettext) {
    var ctrl = this;
    ctrl.schemaParses = true;
    ctrl.formParses = true;
    ctrl.availableForms = [
      {
        name: gettext("Text Inputs"),
        data: basePath + 'example-forms/text-inputs.json'
      },
      {
        name: gettext("Buttons"),
        data: basePath + 'example-forms/buttons.json'
      },
      {
        name: gettext("Radios, Checkboxes and Select"),
        data: basePath + 'example-forms/radios-checkboxes-select.json'
      },
      {
        name: gettext("Sections and Fieldsets"),
        data: basePath + 'example-forms/sections-fieldsets.json'
      },
      {
        name: gettext("Tabs"),
        data: basePath + 'example-forms/tabs.json'
      },
      {
        name: gettext("Add Ons, Required and Feedback"),
        data: basePath + 'example-forms/addons-required-feedback.json'
      },
      {
        name: gettext("Array"),
        data: basePath + 'example-forms/array.json'
      },
      {
        name: gettext("Tab Array"),
        data: basePath + 'example-forms/tabarray.json'
      },
      {
        name: gettext("A Confirmation Dialog"),
        data: basePath + 'example-forms/confirmation-dialog.json'
      }
    ];
    ctrl.selectedForm = ctrl.availableForms[0];
    ctrl.model = {};

    ctrl.formJson = JSON.stringify(ctrl.form, undefined, 2);
    ctrl.schemaJson = JSON.stringify(ctrl.schema, undefined, 2);
    ctrl.launchCurrentFormAsModal = launchCurrentFormAsModal;
    ctrl.viewFormJavascript = viewFormJavascript;

    // Update if user selects a new form example
    $scope.$watch('ctrl.selectedForm',function(item) {
      if (angular.isDefined(item.data)) {
        $http.get(item.data).then(function(result) {
          setNewForm(result.data);
        });
      }
    });

    // Update if user edits schema JSON
    $scope.$watch('ctrl.schemaJson',function(val, old) {
      if (val && val !== old) {
        try {
          ctrl.schema = JSON.parse(ctrl.schemaJson);
          ctrl.schemaParses = true;
        } catch (e) {
          ctrl.schemaParses = false;
          ctrl.schemaError = e.message;
        }
      }
    });

    // Update if the user edits the form JSON
    $scope.$watch('ctrl.formJson', function(val, old){
      if (val && val !== old) {
        try {
          ctrl.form = JSON.parse(ctrl.formJson);
          ctrl.formParses = true;
        } catch (e) {
          ctrl.formParses = false;
          ctrl.formError = e.message;
        }
      }
    });

    // Format the current form model for readability
    ctrl.prettyModelData = function(){
      return typeof ctrl.model === 'string' ? ctrl.model : JSON.stringify(ctrl.model, undefined, 2);
    };

    // Format the current form, schema and model and a single javascript string
    function prettyFormJavascript(){
      // Put the user's form into a JavaScript object, including any current model values
      var currentFormAsObject = {
        schema: JSON.parse(ctrl.schemaJson),
        form: JSON.parse(ctrl.formJson),
        model: ctrl.model
      };
      // Convert that to a string so we can use it as input to a schema form model
      return "var formConfig = " + JSON.stringify(currentFormAsObject, undefined, 2) + ";";
    }

    // Set the builder to loaded form data
    function setNewForm(data) {
      ctrl.schema = data.schema;
      ctrl.form = data.form;
      ctrl.schemaJson = JSON.stringify(ctrl.schema, undefined, 2);
      ctrl.formJson = JSON.stringify(ctrl.form, undefined, 2);
      ctrl.model = data.model || {};
    }

    // Show the user what the current form looks like as a modal
    function launchCurrentFormAsModal() {
      var config = {
        schema: ctrl.schema,
        form: ctrl.form,
        model: ctrl.model
      };
      return modalFormService.open(config);
    }

    // Show the user the current form as javascript for copy-paste
    function viewFormJavascript() {
      // Build a schema form to display the user's form
      var viewJsSchema = {
        "type": "object",
        "properties": {
          "formJs": {
            "type": "string"
          }
        }
      };
      var viewJsForm = [
        {
          "key": "formJs",
          "type": "template",
          "templateUrl": basePath + "form-config-modal.html"
        }
      ];
      var viewJsModel = {
        "formJS": prettyFormJavascript(),
      };
      var config = {
        schema: viewJsSchema,
        form: viewJsForm,
        model: viewJsModel,
        title: gettext("Your Form as JavaScript")
      };
      return modalFormService.open(config);
    }
  }
})();
