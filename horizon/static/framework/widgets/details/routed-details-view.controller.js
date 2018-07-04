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
    'horizon.framework.redirect',
    'horizon.framework.util.actions.action-result.service',
    'horizon.framework.util.navigations.service',
    'horizon.framework.widgets.modal-wait-spinner.service',
    '$location',
    '$q',
    '$routeParams'
  ];

  function controller(
    registry,
    redirect,
    resultService,
    navigationsService,
    spinnerService,
    $location,
    $q,
    $routeParams
  ) {
    var ctrl = this;

    if (!registry.resourceTypes[$routeParams.type]) {
      redirect.notFound();
    }
    ctrl.resourceType = registry.getResourceType($routeParams.type);
    ctrl.context = {};
    ctrl.context.identifier = ctrl.resourceType.parsePath($routeParams.path);
    ctrl.context.loadPromise = ctrl.resourceType.load(ctrl.context.identifier);
    ctrl.context.loadPromise.then(loadData, loadDataError);
    ctrl.defaultTemplateUrl = registry.getDefaultDetailsTemplateUrl();
    ctrl.resultHandler = actionResultHandler;
    ctrl.pageNotFound = redirect.notFound;

    checkRoutedByDjango(ctrl.resourceType);

    function checkRoutedByDjango(resourceType) {
      // get flag that means routed once by django.
      var routedByDjango = angular.element("ngdetails").attr("routed-by-django");
      if (routedByDjango === "True") {
        // If django routed to ngdetails view, navigations (i.e. side bar and
        // breadcrumbs) are set as default dashboard and panel by django side
        // AngularDetailsView.
        // So reset navigations properly using defaultIndexUrl parameter for
        // resource-type-service.

        // get defaultIndexUrl
        var url = resourceType.getDefaultIndexUrl();
        // if querystring has 'nav' parameter, overwrite the url
        var query = $location.search();
        if (query.hasOwnProperty("nav")) {
          url = query.nav;
        }
        // check navigation from url
        if (!navigationsService.isNavigationExists(url)) {
          pageNotFound();
        }
        // set navigations (side bar and breadcrumb)
        var labels = navigationsService.expandNavigationByUrl(url);
        navigationsService.setBreadcrumb(labels);

        // clear flag
        angular.element("ngdetails").removeAttr("routed-by-django");
      }
    }

    function actionResultHandler(returnValue) {
      return $q.when(returnValue, actionSuccessHandler);
    }

    function loadData(response) {
      spinnerService.hideModalSpinner();
      ctrl.showDetails = true;
      ctrl.resourceType.initActions();
      ctrl.itemData = response.data;
      ctrl.itemName = ctrl.resourceType.itemName(response.data);
    }

    function loadDataError(error) {
      if (error.status === 404) {
        redirect.notFound();
      }
    }

    function loadIndexView() {
      spinnerService.hideModalSpinner();
      ctrl.showDetails = false;
      var url = navigationsService.getActivePanelUrl();
      $location.url(url);
    }

    function actionSuccessHandler(result) {
      // The action has completed (for whatever "complete" means to that
      // action. Notice the view doesn't really need to know the semantics of the
      // particular action because the actions return data in a standard form.
      // That return includes the id and type of each created, updated, deleted
      // and failed item.
      // Currently just refreshes the display each time.
      if (result.failed && result.deleted &&
          result.failed.length === 0 && result.deleted.length > 0) {
        loadIndexView();
      } else if (result) {
        spinnerService.showModalSpinner(gettext('Please Wait'));
        ctrl.showDetails = false;
        ctrl.context.loadPromise = ctrl.resourceType.load(ctrl.context.identifier);
        return ctrl.context.loadPromise.then(loadData);
      }
    }
  }

})();
