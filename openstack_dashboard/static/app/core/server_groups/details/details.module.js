/*
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

(function() {
  'use strict';

  /**
   * @ngdoc overview
   * @ngname horizon.app.core.server_groups.details
   *
   * @description
   * Provides details features for server groups.
   */
  angular
    .module('horizon.app.core.server_groups.details', [
      'horizon.framework.conf',
      'horizon.app.core'
    ])
   .run(registerServerGroupDetails);

  registerServerGroupDetails.$inject = [
    'horizon.app.core.server_groups.basePath',
    'horizon.app.core.server_groups.resourceType',
    'horizon.app.core.server_groups.service',
    'horizon.framework.conf.resource-type-registry.service'
  ];

  function registerServerGroupDetails(
    basePath,
    serverGroupResourceType,
    serverGroupService,
    registry
  ) {
    registry.getResourceType(serverGroupResourceType)
      .setLoadFunction(serverGroupService.getServerGroupPromise)
      .detailsViews.append({
        id: 'serverGroupDetailsOverview',
        name: gettext('Overview'),
        template: basePath + 'details/overview.html'
      });
  }

})();
