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

  angular
    .module('horizon.app.core.server_groups')
    .factory('horizon.app.core.server_groups.actions.delete.service', deleteServerGroupService);

  deleteServerGroupService.$inject = [
    '$location',
    'horizon.app.core.openstack-service-api.nova',
    'horizon.app.core.openstack-service-api.policy',
    'horizon.app.core.server_groups.resourceType',
    'horizon.framework.util.actions.action-result.service',
    'horizon.framework.util.i18n.ngettext',
    'horizon.framework.widgets.modal.deleteModalService'
  ];

  /*
   * @ngdoc factory
   * @name horizon.app.core.server_groups.actions.delete.service
   *
   * @Description
   * Brings up the delete server groups confirmation modal dialog.

   * On submit, delete given server groups.
   * On cancel, do nothing.
   */
  function deleteServerGroupService(
    $location,
    nova,
    policy,
    serverGroupResourceType,
    actionResultService,
    ngettext,
    deleteModal
  ) {
    return {
      allowed: allowed,
      perform: perform
    };

    //////////////

    function allowed() {
      return policy.ifAllowed(
        {rules: [['compute', 'os_compute_api:os-server-groups:delete']]});
    }

    function perform(items, scope) {
      var servergroups = angular.isArray(items) ? items : [items];
      var context = {
        labels: labelize(servergroups.length),
        deleteEntity: deleteServerGroup
      };
      return deleteModal.open(scope, servergroups, context).then(deleteResult);
    }

    function deleteResult(deleteModalResult) {
      // To make the result of this action generically useful, reformat the return
      // from the deleteModal into a standard form
      var actionResult = actionResultService.getActionResult();
      deleteModalResult.pass.forEach(function markDeleted(item) {
        actionResult.deleted(serverGroupResourceType, item.context.id);
      });
      deleteModalResult.fail.forEach(function markFailed(item) {
        actionResult.failed(serverGroupResourceType, item.context.id);
      });
      var path = '/project/server_groups';
      if ($location.url() !== path && actionResult.result.failed.length === 0 &&
          actionResult.result.deleted.length > 0) {
        $location.path(path);
      } else {
        return actionResult.result;
      }
    }

    function labelize(count) {
      return {
        title: ngettext(
          'Confirm Delete Server Group',
          'Confirm Delete Server Groups', count),
        message: ngettext(
          'You have selected "%s". Deleted Server Group is not recoverable.',
          'You have selected "%s". Deleted Server Groups are not recoverable.', count),
        submit: ngettext(
          'Delete Server Group',
          'Delete Server Groups', count),
        success: ngettext(
          'Deleted Server Group: %s.',
          'Deleted Server Groups: %s.', count),
        error: ngettext(
          'Unable to delete Server Group: %s.',
          'Unable to delete Server Groups: %s.', count)
      };

    }

    function deleteServerGroup(servergroup) {
      return nova.deleteServerGroup(servergroup, true);
    }
  }
})();
