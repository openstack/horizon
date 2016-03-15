/*
 *    (c) Copyright 2016 Rackspace US, Inc
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
   * @name horizon.dashboard.project.containers.ContainersController
   *
   * @description
   * Controller for the interface around a list of containers for a single account.
   */
  angular
    .module('horizon.dashboard.project.containers')
    .controller('horizon.dashboard.project.containers.ContainersController', ContainersController);

  ContainersController.$inject = [
    'horizon.app.core.openstack-service-api.swift',
    'horizon.dashboard.project.containers.containers-model',
    'horizon.dashboard.project.containers.basePath',
    'horizon.dashboard.project.containers.baseRoute',
    'horizon.dashboard.project.containers.containerRoute',
    'horizon.framework.widgets.modal.simple-modal.service',
    'horizon.framework.widgets.toast.service',
    '$location',
    '$modal'
  ];

  function ContainersController(swiftAPI, containersModel, basePath, baseRoute, containerRoute,
                                simpleModalService, toastService, $location, $modal)
  {
    var ctrl = this;
    ctrl.model = containersModel;
    ctrl.model.initialize();
    ctrl.baseRoute = baseRoute;
    ctrl.containerRoute = containerRoute;

    ctrl.toggleAccess = toggleAccess;
    ctrl.deleteContainer = deleteContainer;
    ctrl.deleteContainerAction = deleteContainerAction;
    ctrl.createContainer = createContainer;
    ctrl.createContainerAction = createContainerAction;
    ctrl.selectContainer = selectContainer;

    //////////

    function selectContainer(container) {
      ctrl.model.container = container;
      $location.path(ctrl.containerRoute + container.name);
      return ctrl.model.fetchContainerDetail(container);
    }

    function toggleAccess(container) {
      swiftAPI.setContainerAccess(container.name, container.is_public).then(
        function updated() {
          var access = 'private';
          if (container.is_public) {
            access = 'public';
          }
          toastService.add('success', interpolate(
            gettext('Container %(name)s is now %(access)s.'),
            {name: container.name, access: access},
            true
          ));

          // re-fetch container details
          ctrl.model.fetchContainerDetail(container, true);
        },
        function failure() {
          container.is_public = !container.is_public;
        });
    }

    function deleteContainer(container) {
      var options = {
        title: gettext('Confirm Delete'),
        body: interpolate(
          gettext('Are you sure you want to delete container %(name)s?'), container, true
          ),
        submit: gettext('Yes'),
        cancel: gettext('No')
      };

      simpleModalService.modal(options).result.then(function confirmed() {
        return ctrl.deleteContainerAction(container);
      });
    }

    function deleteContainerAction(container) {
      swiftAPI.deleteContainer(container.name).then(
        function deleted() {
          toastService.add('success', interpolate(
            gettext('Container %(name)s deleted.'), container, true
          ));

          // remove the deleted container from the containers list
          for (var i = ctrl.model.containers.length - 1; i >= 0; i--) {
            if (ctrl.model.containers[i].name === container.name) {
              ctrl.model.containers.splice(i, 1);
              break;
            }
          }

          // route back to no selected container if we deleted the current one
          if (ctrl.model.container.name === container.name) {
            $location.path(ctrl.baseRoute);
          }
        });
    }

    function createContainer() {
      var localSpec = {
        backdrop: 'static',
        controller: 'CreateContainerModalController as ctrl',
        templateUrl: basePath + 'create-container-modal.html'
      };
      $modal.open(localSpec).result.then(function create(result) {
        return ctrl.createContainerAction(result);
      });
    }

    function createContainerAction(result) {
      swiftAPI.createContainer(result.name, result.public).then(
        function success() {
          toastService.add('success', interpolate(
            gettext('Container %(name)s created.'), result, true
          ));
          // generate a table row with no contents
          ctrl.model.containers.push({name: result.name, count: 0, bytes: 0});
        }
      );
    }
  }
})();
