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
    .module('horizon.app.core.network_qos')
    .factory('horizon.app.core.network_qos.actions.delete.service', deleteService);

  deleteService.$inject = [
    '$q',
    'horizon.app.core.openstack-service-api.neutron',
    'horizon.app.core.openstack-service-api.policy',
    'horizon.app.core.network_qos.resourceType',
    'horizon.framework.util.actions.action-result.service',
    'horizon.framework.widgets.modal.deleteModalService'
  ];

  function deleteService(
    $q,
    neutron,
    policy,
    resourceType,
    actionResultService,
    deleteModal
  ) {
    var service = {
      allowed: allowed,
      perform: perform
    };

    return service;

    ////////////

    function allowed() {
      return policy.ifAllowed(
        {rules: [
          ['network', 'delete_qos_policy']
        ]}
      );
    }

    function perform(items, scope) {
      var policies = angular.isArray(items) ? items : [items];

      return openModal().then(onComplete);

      function openModal() {
        return deleteModal.open(
          scope,
          policies,
          {
            labels: labelize(policies.length),
            deleteEntity: neutron.deletePolicy
          }
        );
      }

      function onComplete(result) {
        var actionResult = actionResultService.getActionResult();

        result.pass.forEach(function markDeleted(item) {
          actionResult.deleted(resourceType, item.context.id);
        });
        result.fail.forEach(function markFailed(item) {
          actionResult.failed(resourceType, item.context.id);
        });

        return actionResult.result;
      }
    }

    function labelize(count) {
      return {
        title: ngettext(
          'Confirm Delete Policy',
          'Confirm Delete Policies',
          count),

        message: ngettext(
          'You have selected "%s". Deleted policy is not recoverable.',
          'You have selected "%s". Deleted policies are not recoverable.',
          count),

        submit: ngettext(
          'Delete Policy',
          'Delete Policies',
          count),

        success: ngettext(
          'Deleted policy: %s.',
          'Deleted policies: %s.',
          count),

        error: ngettext(
          'Unable to delete policy: %s.',
          'Unable to delete policies: %s.',
          count)
      };
    }

  }

})();
