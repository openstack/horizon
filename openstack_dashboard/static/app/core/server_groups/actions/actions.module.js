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
   * @ngname horizon.app.core.server_groups.actions
   *
   * @description
   * Provides all of the actions for server groups.
   */
  angular
    .module('horizon.app.core.server_groups.actions', [
      'horizon.framework.conf',
      'horizon.app.core.server_groups'
    ])
    .run(registerServerGroupActions);

  registerServerGroupActions.$inject = [
    'horizon.app.core.server_groups.actions.create.service',
    'horizon.app.core.server_groups.actions.delete.service',
    'horizon.app.core.server_groups.resourceType',
    'horizon.framework.conf.resource-type-registry.service'
  ];

  function registerServerGroupActions(
    createService,
    deleteService,
    serverGroupResourceTypeCode,
    registry
  ) {
    var serverGroupResourceType = registry.getResourceType(serverGroupResourceTypeCode);

    serverGroupResourceType.itemActions
      .append({
        id: 'deleteServerGroupAction',
        service: deleteService,
        template: {
          type: 'delete',
          text: gettext('Delete Server Group')
        }
      });

    serverGroupResourceType.batchActions
      .append({
        id: 'batchDeleteServerGroupAction',
        service: deleteService,
        template: {
          type: 'delete-selected',
          text: gettext('Delete Server Groups')
        }
      });

    serverGroupResourceType.globalActions
      .append({
        id: 'createServerGroupAction',
        service: createService,
        template: {
          type: 'create',
          text: gettext('Create Server Group')
        }
      });
  }

})();
