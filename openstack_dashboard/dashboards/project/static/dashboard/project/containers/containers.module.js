/**
 *    (c) Copyright 2015 Rackspace, US, Inc.
 *
 * Licensed under the Apache License, Version 2.0 (the "License"); you may
 * not use this file except in compliance with the License. You may obtain
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

  /**
   * @ngdoc overview
   * @ngname horizon.dashboard.project.containers
   *
   * @description
   * Provides the services and widgets required
   * to support and display the project containers panel.
   */
  angular
    .module('horizon.dashboard.project.containers', ['ngRoute'])
    .config(config);

  config.$inject = [
    '$provide',
    '$routeProvider',
    '$windowProvider'
  ];

  /**
   * @name horizon.dashboard.project.containers.basePath
   * @description Base path for the project dashboard
   */
  function config($provide, $routeProvider, $windowProvider) {
    var path = $windowProvider.$get().STATIC_URL + 'dashboard/project/containers/';
    $provide.constant('horizon.dashboard.project.containers.basePath', path);

    var baseRoute = 'project/containers/';
    $provide.constant('horizon.dashboard.project.containers.baseRoute', baseRoute);

    var containerRoute = baseRoute + 'container/';
    $provide.constant('horizon.dashboard.project.containers.containerRoute', containerRoute);

    $routeProvider
      .when('/' + baseRoute, {
        templateUrl: path + 'select-container.html'
      })
      .when('/' + containerRoute + ':container', {
        templateUrl: path + 'objects.html'
      })
      .when('/' + containerRoute + ':container/:folder*', {
        templateUrl: path + 'objects.html'
      });
  }
})();
