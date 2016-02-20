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
   * @ngdoc overview
   * @name horizon.app.core
   * @description
   *
   * # horizon.app.core
   *
   * This module hosts modules of core functionality and services that supports
   * components added to Horizon via its plugin mechanism.
   */
  angular
    .module('horizon.app.core', [
      'horizon.app.core.cloud-services',
      'horizon.app.core.images',
      'horizon.app.core.metadata',
      'horizon.app.core.openstack-service-api',
      'horizon.app.core.workflow',
      'horizon.framework.conf',
      'horizon.framework.util',
      'horizon.framework.widgets',
      'horizon.dashboard.project.workflow'
    ], config);

  config.$inject = ['$provide', '$windowProvider'];

  function config($provide, $windowProvider) {
    var path = $windowProvider.$get().STATIC_URL + 'app/core/';
    $provide.constant('horizon.app.core.basePath', path);
  }

})();
