/**
 * Copyright 2017 99Cloud
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
   * @ngname horizon.dashboard.identity.groups.actions
   *
   * @description
   * Provides all of the actions for groups.
   */
  angular
    .module('horizon.dashboard.identity.groups.actions', [
      'horizon.framework.conf'
    ])
    .run(registerGroupActions);

  registerGroupActions.$inject = [
    'horizon.framework.conf.resource-type-registry.service',
    'horizon.dashboard.identity.groups.actions.create.service',
    'horizon.dashboard.identity.groups.actions.delete.service',
    'horizon.dashboard.identity.groups.actions.edit.service',
    'horizon.dashboard.identity.groups.resourceType'
  ];

  function registerGroupActions(
    registry,
    createService,
    deleteService,
    editService,
    groupResourceTypeCode
  ) {
    var groupResourceType = registry.getResourceType(groupResourceTypeCode);

    groupResourceType.itemActions
      .append({
        id: 'editAction',
        service: editService,
        template: {
          text: gettext('Edit Group')
        }
      })
      .append({
        id: 'deleteAction',
        service: deleteService,
        template: {
          text: gettext('Delete Group'),
          type: 'delete'
        }
      });

    groupResourceType.batchActions
      .append({
        id: 'batchDeleteAction',
        service: deleteService,
        template: {
          type: 'delete-selected',
          text: gettext('Delete Groups')
        }
      });

    groupResourceType.globalActions
      .append({
        id: 'createGroupAction',
        service: createService,
        template: {
          type: 'create',
          text: gettext('Create Group')
        }
      });
  }

})();
