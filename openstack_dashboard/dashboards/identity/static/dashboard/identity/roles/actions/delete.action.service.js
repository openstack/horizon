/**
 * Copyright 2016 99Cloud
 *
 * Licensed under the Apache License, Version 2.0 (the "License"); you may
 * not use self file except in compliance with the License. You may obtain
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

  angular
    .module('horizon.dashboard.identity.roles')
    .factory('horizon.dashboard.identity.roles.actions.delete.service', deleteRoleService);

  deleteRoleService.$inject = [
    '$q',
    'horizon.app.core.openstack-service-api.keystone',
    'horizon.app.core.openstack-service-api.policy',
    'horizon.framework.util.actions.action-result.service',
    'horizon.framework.util.i18n.ngettext',
    'horizon.framework.widgets.modal.deleteModalService',
    'horizon.dashboard.identity.roles.resourceType'
  ];

  /*
   * @ngdoc factory
   * @name horizon.dashboard.identity.roles.actions.delete.service
   *
   * @Description
   * Brings up the delete roles confirmation modal dialog.

   * On submit, delete given roles.
   * On cancel, do nothing.
   */
  function deleteRoleService(
    $q,
    keystone,
    policy,
    actionResultService,
    ngettext,
    deleteModal,
    roleResourceType
  ) {
    return {
      allowed: allowed,
      perform: perform,
      deleteResult: deleteResult  // exposed just for testing
    };

    //////////////

    function allowed() {
      return $q.all([
        keystone.canEditIdentity('role'),
        policy.ifAllowed({ rules: [['identity', 'identity:delete_role']] })
      ]);
    }

    function perform(items, scope) {
      var roles = angular.isArray(items) ? items : [items];
      var context = {
        labels: labelize(roles.length),
        deleteEntity: function deleteRole(role) {
          return keystone.deleteRole(role);
        }
      };
      return deleteModal.open(scope, roles, context).then(deleteResult);
    }

    function deleteResult(deleteModalResult) {
      // To make the result of this action generically useful, reformat the return
      // from the deleteModal into a standard form
      var actionResult = actionResultService.getActionResult();
      deleteModalResult.pass.forEach(function markDeleted(item) {
        actionResult.deleted(roleResourceType, item.context.id);
      });
      deleteModalResult.fail.forEach(function markFailed(item) {
        actionResult.failed(roleResourceType, item.context.id);
      });
      return actionResult.result;
    }

    function labelize(count) {
      return {
        title: ngettext(
          'Confirm Delete Role',
          'Confirm Delete Roles', count),
        message: ngettext(
          'You have selected "%s". Deleted role is not recoverable.',
          'You have selected "%s". Deleted roles are not recoverable.', count),
        submit: ngettext(
          'Delete Role',
          'Delete Roles', count),
        success: ngettext(
          'Deleted Role: %s.',
          'Deleted Roles: %s.', count),
        error: ngettext(
          'Unable to delete Role: %s.',
          'Unable to delete Roles: %s.', count)
      };
    }
  }
})();
