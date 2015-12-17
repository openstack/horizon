/*
 *    (c) Copyright 2015 Hewlett-Packard Development Company, L.P.
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
   * @ngname horizon.dashboard.project
   * @description
   * Dashboard module to host project panels.
   */
  angular
    .module('horizon.dashboard.project', [
      'horizon.dashboard.project.containers',
      'horizon.dashboard.project.images',
      'horizon.dashboard.project.workflow'
    ])
    .config(config);

  config.$inject = [
    '$provide',
    '$windowProvider'
  ];

  /**
   * @name horizon.dashboard.project.basePath
   * @description Base path for the project dashboard
   */
  function config($provide, $windowProvider) {
    var path = $windowProvider.$get().STATIC_URL + 'dashboard/project/';
    $provide.constant('horizon.dashboard.project.basePath', path);
  }

})();
