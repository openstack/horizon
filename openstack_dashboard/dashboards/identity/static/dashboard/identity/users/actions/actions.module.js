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
   * @ngname horizon.dashboard.identity.users.actions
   *
   * @description
   * Provides all of the actions for users.
   */
  angular
    .module('horizon.dashboard.identity.users.actions', [
      'horizon.framework.conf'
    ])
    .run(registerUserActions)
    .config(config);

  registerUserActions.$inject = [
    'horizon.framework.conf.resource-type-registry.service',
    'horizon.dashboard.identity.users.actions.create.service',
    'horizon.dashboard.identity.users.actions.update.service',
    'horizon.dashboard.identity.users.actions.password.service',
    'horizon.dashboard.identity.users.actions.enable.service',
    'horizon.dashboard.identity.users.actions.disable.service',
    'horizon.dashboard.identity.users.actions.delete.service',
    'horizon.dashboard.identity.users.resourceType'
  ];

  function registerUserActions(
    registry,
    createService,
    updateService,
    passwordService,
    enableService,
    disableService,
    deleteService,
    userResourceTypeCode
  ) {
    var userResourceType = registry.getResourceType(userResourceTypeCode);

    userResourceType.itemActions
      .append({
        id: 'updateAction',
        service: updateService,
        template: {
          text: gettext('Edit User'),
          type: 'row'
        }
      })
      .append({
        id: 'passwordAction',
        service: passwordService,
        template: {
          text: gettext('Change Password'),
          type: 'row'
        }
      })
      .append({
        id: 'enableAction',
        service: enableService,
        template: {
          text: gettext('Enable User'),
          type: 'row'
        }
      })
      .append({
        id: 'disableAction',
        service: disableService,
        template: {
          text: gettext('Disable User'),
          type: 'row'
        }
      })
      .append({
        id: 'deleteAction',
        service: deleteService,
        template: {
          text: gettext('Delete User'),
          type: 'delete'
        }
      });

    userResourceType.batchActions
      .append({
        id: 'batchDeleteAction',
        service: deleteService,
        template: {
          type: 'delete-selected',
          text: gettext('Delete Users')
        }
      });

    userResourceType.globalActions
      .append({
        id: 'createUserAction',
        service: createService,
        template: {
          type: 'create',
          text: gettext('Create User')
        }
      });
  }

  config.$inject = [
    '$provide',
    '$windowProvider'
  ];

  function config($provide, $windowProvider) {
    var path = $windowProvider.$get().STATIC_URL + 'dashboard/identity/users/actions/';
    $provide.constant('horizon.dashboard.identity.users.actions.basePath', path);
  }
})();
