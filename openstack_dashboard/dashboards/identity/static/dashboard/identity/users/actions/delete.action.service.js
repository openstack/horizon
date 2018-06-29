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
    .module('horizon.dashboard.identity.users')
    .factory('horizon.dashboard.identity.users.actions.delete.service', deleteUserService);

  deleteUserService.$inject = [
    '$q',
    'horizon.app.core.openstack-service-api.keystone',
    'horizon.app.core.openstack-service-api.policy',
    'horizon.framework.util.actions.action-result.service',
    'horizon.framework.util.i18n.gettext',
    'horizon.framework.widgets.modal.deleteModalService',
    'horizon.framework.widgets.toast.service',
    'horizon.dashboard.identity.users.resourceType'
  ];

  /*
   * @ngdoc factory
   * @name horizon.dashboard.identity.users.actions.delete.service
   *
   * @Description
   * Brings up the delete users confirmation modal dialog.

   * On submit, delete given users.
   * On cancel, do nothing.
   */
  function deleteUserService(
    $q,
    keystone,
    policy,
    actionResultService,
    gettext,
    deleteModal,
    toast,
    userResourceType
  ) {
    var service = {
      allowed: allowed,
      perform: perform,
      deleteResult: deleteResult
    };

    return service;

    //////////////

    function allowed() {
      return $q.all([
        keystone.canEditIdentity('user'),
        policy.ifAllowed({ rules: [['identity', 'identity:delete_user']] })
      ]);
    }

    function perform(items, scope) {
      var users = angular.isArray(items) ? items : [items];
      var context = {
        labels: labelize(users.length),
        deleteEntity: deleteUser
      };
      return deleteModal.open(scope, users, context).then(deleteResult);
    }

    function deleteResult(deleteModalResult) {
      // To make the result of this action generically useful, reformat the return
      // from the deleteModal into a standard form
      var actionResult = actionResultService.getActionResult();
      deleteModalResult.pass.forEach(function markDeleted(item) {
        actionResult.deleted(userResourceType, item.context.id);
      });
      deleteModalResult.fail.forEach(function markFailed(item) {
        actionResult.failed(userResourceType, item.context.id);
      });
      return actionResult.result;
    }

    function labelize(count) {
      return {

        title: ngettext(
          'Confirm Delete User',
          'Confirm Delete Users', count),

        message: ngettext(
          'You have selected "%s". Deleted user is not recoverable.',
          'You have selected "%s". Deleted users are not recoverable.', count),

        submit: ngettext(
          'Delete User',
          'Delete Users', count),

        success: ngettext(
          'Deleted User: %s.',
          'Deleted Users: %s.', count),

        error: ngettext(
          'Unable to delete User: %s.',
          'Unable to delete Users: %s.', count)
      };
    }

    function deleteUser(user) {
      return keystone.deleteUser(user);
    }

  }
})();
