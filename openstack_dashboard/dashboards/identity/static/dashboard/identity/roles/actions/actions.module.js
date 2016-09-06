/**
 * Copyright 2016 99Cloud
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
   * @ngname horizon.dashboard.identity.roles.actions
   *
   * @description
   * Provides all of the actions for roles.
   */
  angular
    .module('horizon.dashboard.identity.roles.actions', [
      'horizon.framework.conf'
    ])
    .run(registerRoleActions);

  registerRoleActions.$inject = [
    'horizon.framework.conf.resource-type-registry.service',
    'horizon.dashboard.identity.roles.actions.create.service',
    'horizon.dashboard.identity.roles.actions.delete.service',
    'horizon.dashboard.identity.roles.actions.edit.service',
    'horizon.dashboard.identity.roles.resourceType'
  ];

  function registerRoleActions(
    registry,
    createService,
    deleteService,
    editService,
    roleResourceTypeCode
  ) {
    var roleResourceType = registry.getResourceType(roleResourceTypeCode);

    roleResourceType.itemActions
      .append({
        id: 'editRoleAction',
        service: editService,
        template: {
          text: gettext('Edit Role')
        }
      })
      .append({
        id: 'deleteAction',
        service: deleteService,
        template: {
          text: gettext('Delete Role'),
          type: 'delete'
        }
      });

    roleResourceType.batchActions
      .append({
        id: 'batchDeleteAction',
        service: deleteService,
        template: {
          type: 'delete-selected',
          text: gettext('Delete Roles')
        }
      });

    roleResourceType.globalActions
      .append({
        id: 'createRoleAction',
        service: createService,
        template: {
          type: 'create',
          text: gettext('Create Role')
        }
      });
  }

})();
