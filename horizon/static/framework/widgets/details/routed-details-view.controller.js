/*
 * (c) Copyright 2016 Hewlett Packard Enterprise Development Company LP
 *
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
(function() {
  "use strict";

  angular
    .module('horizon.framework.widgets.details')
    .controller('RoutedDetailsViewController', controller);

  controller.$inject = [
    'horizon.framework.conf.resource-type-registry.service',
    'horizon.framework.util.actions.action-result.service',
    'horizon.framework.widgets.modal-wait-spinner.service',
    '$q',
    '$routeParams',
    '$rootScope'
  ];

  function controller(
    registry,
    resultService,
    spinnerService,
    $q,
    $routeParams,
    $rootScope
  ) {
    var ctrl = this;

    ctrl.resourceType = registry.getResourceType($routeParams.type);
    ctrl.context = ctrl.resourceType.parsePath($routeParams.path);
    ctrl.context.loadPromise = ctrl.resourceType.load(ctrl.context.identifier);
    ctrl.context.loadPromise.then(loadData);
    ctrl.defaultTemplateUrl = registry.getDefaultDetailsTemplateUrl();
    ctrl.resultHandler = actionResultHandler;

    function actionResultHandler(returnValue) {
      return $q.when(returnValue, actionSuccessHandler);
    }

    function loadData(response) {
      spinnerService.hideModalSpinner();
      ctrl.showDetails = true;
      registry.initActions($routeParams.type, $rootScope.$new());
      ctrl.itemData = response.data;
      ctrl.itemName = ctrl.resourceType.itemName(response.data);
    }

    function actionSuccessHandler(result) {
      // The action has completed (for whatever "complete" means to that
      // action. Notice the view doesn't really need to know the semantics of the
      // particular action because the actions return data in a standard form.
      // That return includes the id and type of each created, updated, deleted
      // and failed item.
      // Currently just refreshes the display each time.
      if (result) {
        spinnerService.showModalSpinner(gettext('Please Wait'));
        ctrl.showDetails = false;
        ctrl.context.loadPromise = ctrl.resourceType.load(ctrl.context.identifier);
        ctrl.context.loadPromise.then(loadData);
      }
    }
  }

})();
