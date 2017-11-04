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

  // Constants used within this file
  var VOLUME_RESOURCE_TYPE = 'OS::Cinder::Volume';

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
      'horizon.app.core.conf',
      'horizon.app.core.constants',
      'horizon.app.core.cloud-services',
      'horizon.app.core.flavors',
      'horizon.app.core.images',
      'horizon.app.core.keypairs',
      'horizon.app.core.metadata',
      'horizon.app.core.network_qos',
      'horizon.app.core.openstack-service-api',
      'horizon.app.core.server_groups',
      'horizon.app.core.trunks',
      'horizon.app.core.workflow',
      'horizon.framework.conf',
      'horizon.framework.util',
      'horizon.framework.widgets',
      'horizon.dashboard.project.workflow'
    ], config)
    // NOTE: this will move into the correct module as that resource type
    // becomes available.  For now there is no volumes module.
    .constant('horizon.app.core.volumes.resourceType', VOLUME_RESOURCE_TYPE);

  config.$inject = [
    '$provide',
    '$windowProvider',
    '$routeProvider',
    'horizon.app.core.detailRoute'
  ];

  function config($provide, $windowProvider, $routeProvider, detailRoute) {
    var path = $windowProvider.$get().STATIC_URL + 'app/core/';
    $provide.constant('horizon.app.core.basePath', path);

    $routeProvider
      .when('/' + detailRoute + ':type/:path*', {
        templateUrl: $windowProvider.$get().STATIC_URL +
          'framework/widgets/details/routed-details-view.html'
      });
  }

})();
