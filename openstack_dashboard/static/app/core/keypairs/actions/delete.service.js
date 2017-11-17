/**
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
    .module('horizon.app.core.keypairs')
    .factory('horizon.app.core.keypairs.actions.delete.service', deleteService);

  deleteService.$inject = [
    '$location',
    'horizon.app.core.keypairs.resourceType',
    'horizon.app.core.openstack-service-api.nova',
    'horizon.app.core.openstack-service-api.policy',
    'horizon.framework.util.actions.action-result.service',
    'horizon.framework.util.i18n.gettext',
    'horizon.framework.widgets.modal.deleteModalService'
  ];

  /*
   * @ngdoc factory
   * @name horizon.app.core.keypairs.actions.delete.service
   *
   * @Description
   * Brings up the delete keypairs confirmation modal dialog.

   * On submit, delete given keypairs.
   * On cancel, do nothing.
   */
  function deleteService(
    $location,
    resourceType,
    nova,
    policy,
    actionResultService,
    gettext,
    deleteModal
  ) {

    var service = {
      allowed: allowed,
      perform: perform
    };

    return service;

    //////////////

    function allowed() {
      return policy.ifAllowed({ rules: [['compute', 'os_compute_api:os-keypairs:delete']] });
    }

    function perform(items, scope) {
      var keypairs = angular.isArray(items) ? items : [items];
      var context = {
        labels: labelize(keypairs.length),
        deleteEntity: deleteKeypair
      };
      return deleteModal.open(scope, keypairs, context).then(deleteResult);
    }

    function deleteResult(deleteModalResult) {
      // To make the result of this action generically useful, reformat the return
      // from the deleteModal into a standard form
      var actionResult = actionResultService.getActionResult();
      deleteModalResult.pass.forEach(function markDeleted(item) {
        actionResult.deleted(resourceType, item.context.id);
      });
      deleteModalResult.fail.forEach(function markFailed(item) {
        actionResult.failed(resourceType, item.context.id);
      });

      var path = '/project/key_pairs';
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
          'Confirm Delete Key Pair',
          'Confirm Delete Key Pairs', count),

        message: ngettext(
          'You have selected "%s". Deleted key pair is not recoverable.',
          'You have selected "%s". Deleted key pairs are not recoverable.', count),

        submit: ngettext(
          'Delete Key Pair',
          'Delete Key Pairs', count),

        success: ngettext(
          'Deleted Key Pair: %s.',
          'Deleted Key Pairs: %s.', count),

        error: ngettext(
          'Unable to delete Key Pair: %s.',
          'Unable to delete Key Pairs: %s.', count)
      };
    }

    function deleteKeypair(keypair) {
      return nova.deleteKeypair(keypair, true);
    }
  }
})();
