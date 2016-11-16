/*
 *    (c) Copyright 2015 Rackspace US, Inc
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

(function () {
  'use strict';

  /**
   * @ngdoc controller
   *
   * @name horizon.dashboard.project.containers.ObjectsController
   *
   * @description
   * Controller for the interface around the objects in a single container.
   */
  angular
    .module('horizon.dashboard.project.containers')
    .controller('horizon.dashboard.project.containers.ObjectsController', ObjectsController);

  ObjectsController.$inject = [
    'horizon.framework.conf.resource-type-registry.service',
    'horizon.dashboard.project.containers.containers-model',
    'horizon.dashboard.project.containers.containerRoute',
    'horizon.dashboard.project.containers.object.resourceType',
    'horizon.framework.widgets.table.events',
    '$q',
    '$routeParams',
    '$scope'
  ];

  function ObjectsController(registryService,
                             containersModel,
                             containerRoute,
                             objectResCode,
                             hzTableEvents,
                             $q,
                             $routeParams,
                             $scope) {
    var ctrl = this;
    var objectResourceType = registryService.getResourceType(objectResCode);

    ctrl.rowActions = objectResourceType.itemActions;
    ctrl.batchActions = objectResourceType.batchActions;

    ctrl.model = containersModel;
    ctrl.numSelected = 0;

    ctrl.containerURL = containerRoute + encodeURIComponent($routeParams.container) +
      ctrl.model.DELIMETER;
    if (angular.isDefined($routeParams.folder)) {
      ctrl.currentURL = ctrl.containerURL + encodeURIComponent($routeParams.folder) +
        ctrl.model.DELIMETER;
    } else {
      ctrl.currentURL = ctrl.containerURL;
    }

    ctrl.breadcrumbs = [];

    // ensure that the base model data is loaded and then run our path-based
    // container selection
    ctrl.model.intialiseDeferred.promise.then(function afterInitialise() {
      ctrl.model.selectContainer($routeParams.container, $routeParams.folder)
        .then(function then() {
          ctrl.breadcrumbs = ctrl.getBreadcrumbs();
        });
    });

    ctrl.filterFacets = objectResourceType.filterFacets;

    ctrl.tableConfig = {
      selectAll: true,
      expand: false,
      trackId: 'path',
      columns: objectResourceType.getTableColumns()
    };

    ctrl.getBreadcrumbs = getBreadcrumbs;
    ctrl.objectURL = objectURL;
    ctrl.actionResultHandler = function actionResultHandler(returnValue) {
      return $q.when(returnValue, actionSuccessHandler);
    };

    //////////

    function getBreadcrumbs() {
      var crumbs = [];
      var encoded = ctrl.model.pseudo_folder_hierarchy.map(encodeURIComponent);
      for (var i = 0; i < encoded.length; i++) {
        crumbs.push({
          label: ctrl.model.pseudo_folder_hierarchy[i],
          url: ctrl.containerURL + encoded.slice(0, i + 1).join(ctrl.model.DELIMETER)
        });
      }
      return crumbs;
    }

    function objectURL(file) {
      return ctrl.currentURL + encodeURIComponent(file.name);
    }

    function actionSuccessHandler(result) {
      if (angular.isUndefined(result)) {
        return;
      }
      if (result.deleted.length > 0) {
        $scope.$broadcast(hzTableEvents.CLEAR_SELECTIONS);
        ctrl.model.updateContainer();
        ctrl.model.selectContainer(
          ctrl.model.container.name,
          ctrl.model.folder
        );
      }
    }
  }
})();
