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
    'horizon.dashboard.project.containers.containers-model',
    'horizon.dashboard.project.containers.containerRoute',
    '$routeParams'
  ];

  function ObjectsController(containersModel, containerRoute, $routeParams) {
    var ctrl = this;

    ctrl.model = containersModel;

    ctrl.containerURL = containerRoute + $routeParams.containerName + '/';
    if (angular.isDefined($routeParams.folder)) {
      ctrl.currentURL = ctrl.containerURL + $routeParams.folder + '/';
    } else {
      ctrl.currentURL = ctrl.containerURL;
    }

    ctrl.model.selectContainer($routeParams.containerName, $routeParams.folder);
  }
})();
