/*
 *    (c) Copyright 2016 Mirantis Inc.
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
   * @ngname horizon.dashboard.developer.profiler
   * @description
   * Dashboard module for the profiler panel.
   */
  angular
    .module('horizon.dashboard.developer.profiler', ['ui.bootstrap'])
    .config(config);

  config.$inject = [
    '$provide',
    '$windowProvider',
    '$httpProvider',
    'horizon.dashboard.developer.profiler.headers'
  ];

  function config($provide, $windowProvider, $httpProvider, headers) {
    var path = $windowProvider.$get().STATIC_URL + 'dashboard/developer/profiler/';
    $provide.constant('horizon.dashboard.developer.profiler.basePath', path);
    if (Object.keys(headers).length) {
      $httpProvider.interceptors.push(function() {
        return {
          'request': function(config) {
            if (angular.isUndefined(config.headers)) {
              config.headers = {};
            }
            if (headers) {
              angular.forEach(headers, function(value, key) {
                config.headers[key] = value;
              });
            }
            return config;
          }
        };
      });
    }
  }

})();
