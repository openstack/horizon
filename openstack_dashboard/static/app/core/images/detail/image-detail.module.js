/**
 * (c) Copyright 2016 Hewlett-Packard Development Company, L.P.
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
   * @ngname horizon.app.core.images.details
   *
   * @description
   * Provides details features for images.
   */
  angular.module('horizon.app.core.images.details', ['horizon.framework.conf', 'horizon.app.core'])
   .run(registerImageActions);

  registerImageActions.$inject = [
    'horizon.app.core.images.basePath',
    'horizon.app.core.images.resourceType',
    'horizon.app.core.openstack-service-api.glance',
    'horizon.framework.conf.resource-type-registry.service'
  ];

  function registerImageActions(
    basePath,
    imageResourceType,
    glanceApi,
    registry
  ) {
    registry.getResourceType(imageResourceType).detailsViews
      .append({
        id: 'imageDetailsOverview',
        name: gettext('Overview'),
        template: basePath + 'detail/overview.html'
      });
    registry.getResourceType(imageResourceType)
      .setPathParser(parsePath)
      .setPathGenerator(pathGenerator)
      .setLoadFunction(loadFunction)
      .setDrawerTemplateUrl(basePath + 'detail/drawer.html');

    function pathGenerator(id) {
      return id;
    }

    function parsePath(path) {
      return path;
    }

    function loadFunction(identifier) {
      return glanceApi.getImage(identifier);
    }
  }

})();
