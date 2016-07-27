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

(function () {
  'use strict';

  /**
   * @ngdoc module
   * @ngname horizon.dashboard.developer.form-builder
   * @description
   * Dashboard module for the form-builder panel.
   */
  angular
    .module('horizon.dashboard.developer.form-builder', [], config)
    .constant('horizon.dashboard.developer.form-builder.BASE_ROUTE', '/developer/form_builder/');

  config.$inject = [
    '$provide',
    '$routeProvider',
    '$windowProvider',
    'horizon.dashboard.developer.form-builder.BASE_ROUTE'];

  function config($provide, $routeProvider, $windowProvider, baseRoute) {
    $routeProvider
      .when(baseRoute, {
        templateUrl: $windowProvider.$get().STATIC_URL +
        'dashboard/developer/form-builder/index.html'
      });
    var path = $windowProvider.$get().STATIC_URL + 'dashboard/developer/form-builder/';
    $provide.constant('horizon.dashboard.developer.form-builder.basePath', path);
  }

})();
