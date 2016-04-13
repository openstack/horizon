/**
 * (c) Copyright 2015 Hewlett-Packard Development Company, L.P.
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
   * @ngname horizon.app.core.volume-snapshots
   *
   * @description
   * Provides all of the services and widgets required
   * to support and display instances related content.
   */
  angular
    .module('horizon.app.core.volume-snapshots', ['ngRoute',
      'horizon.app.core.volume-snapshots.actions', 'horizon.app.core.volume-snapshots.details'])
    .constant('horizon.app.core.volume-snapshots.resourceType', 'OS::Cinder::Snapshot')
    .config(config)
    .run(run);

  config.$inject = [ '$provide', '$windowProvider' ];

  function config($provide, $windowProvider) {
    var path = $windowProvider.$get().STATIC_URL + 'app/core/volume-snapshots/';
    $provide.constant('horizon.app.core.volume-snapshots.basePath', path);
  }

  run.$inject = [
    'horizon.framework.conf.resource-type-registry.service',
    'horizon.app.core.volume-snapshots.resourceType'
  ];

  function run(registry, resourceType) {
    registry.getResourceType(resourceType, {
      names: [gettext('Volume Snapshot'), gettext('Volume Snapshots')]
    });
  }

})();
