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
   * @name horizon.dashboard.project.containers.ContainersController
   *
   * @description
   * Controller for the interface around a list of containers for a single account.
   */
  angular
    .module('horizon.dashboard.project.containers')
    .controller('horizon.dashboard.project.containers.ContainersController', ContainersController);

  ContainersController.$inject = [
    'horizon.dashboard.project.containers.containers-model',
    'horizon.dashboard.project.containers.containerRoute',
    '$location'
  ];

  function ContainersController(containersModel, containerRoute, $location) {
    var ctrl = this;
    ctrl.model = containersModel;
    containersModel.initialize();
    ctrl.containerRoute = containerRoute;
    ctrl.selectedContainer = '';

    ctrl.selectContainer = function (name) {
      ctrl.selectedContainer = name;
      $location.path(containerRoute + name);
    };
  }
})();
