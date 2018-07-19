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
    .module('horizon.dashboard.identity.groups')
    .factory('horizon.dashboard.identity.groups.actions.delete.service', deleteGroupService);

  deleteGroupService.$inject = [
    '$q',
    'horizon.app.core.openstack-service-api.keystone',
    'horizon.app.core.openstack-service-api.policy',
    'horizon.framework.util.actions.action-result.service',
    'horizon.framework.widgets.modal.deleteModalService',
    'horizon.dashboard.identity.groups.resourceType'
  ];

  /*
   * @ngdoc factory
   * @name horizon.dashboard.identity.groups.actions.delete.service
   *
   * @Description
   * Brings up the delete groups confirmation modal dialog.

   * On submit, delete given groups.
   * On cancel, do nothing.
   */
  function deleteGroupService(
    $q,
    keystone,
    policy,
    actionResultService,
    deleteModal,
    groupResourceType
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
        keystone.canEditIdentity('group'),
        policy.ifAllowed({ rules: [['identity', 'identity:delete_group']] })
      ]);
    }

    function perform(items, scope) {
      var groups = angular.isArray(items) ? items : [items];
      var context = {
        labels: labelize(groups.length),
        deleteEntity: deleteGroup
      };
      return deleteModal.open(scope, groups, context).then(deleteResult);
    }

    function deleteResult(deleteModalResult) {
      // To make the result of this action generically useful, reformat the return
      // from the deleteModal into a standard form
      var actionResult = actionResultService.getActionResult();
      deleteModalResult.pass.forEach(function markDeleted(item) {
        actionResult.deleted(groupResourceType, item.context.id);
      });
      deleteModalResult.fail.forEach(function markFailed(item) {
        actionResult.failed(groupResourceType, item.context.id);
      });
      return actionResult.result;
    }

    function labelize(count) {
      return {

        title: ngettext(
          'Confirm Delete Group',
          'Confirm Delete Groups', count),

        message: ngettext(
          'You have selected "%s". Deleted group is not recoverable.',
          'You have selected "%s". Deleted groups are not recoverable.', count),

        submit: ngettext(
          'Delete Group',
          'Delete Groups', count),

        success: ngettext(
          'Deleted Group: %s.',
          'Deleted Groups: %s.', count),

        error: ngettext(
          'Unable to delete Group: %s.',
          'Unable to delete Groups: %s.', count)
      };
    }

    function deleteGroup(group) {
      return keystone.deleteGroup(group);
    }

  }
})();
