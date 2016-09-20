/*
 * (c) Copyright 2015 Hewlett Packard Enterprise Development Company LP
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
   * @ngdoc module
   * @ngname horizon.dashboard.developer.resource-browser
   * @description
   * Dashboard module for the resource-browser panel.
   */
  angular
    .module('horizon.dashboard.developer.resource-browser', ['ngRoute', 'schemaForm'], config)
    .constant('horizon.dashboard.developer.resource-browser.BASE_ROUTE',
      'developer/resource_browser/');

  config.$inject = [
    '$windowProvider',
    '$routeProvider',
    'horizon.dashboard.developer.resource-browser.BASE_ROUTE'];

  function config($windowProvider, $routeProvider, baseRoute) {
    $routeProvider
        .when('/' + baseRoute, {
          templateUrl: $windowProvider.$get().STATIC_URL +
          'dashboard/developer/resource-browser/resources.html'
        })
        .when('/' + baseRoute + ':resourceTypeName', {
          template: "<rb-resource-panel></rb-resource-panel>"
        });
  }

})();
