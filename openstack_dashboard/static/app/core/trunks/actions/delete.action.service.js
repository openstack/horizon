/*
 * Copyright 2017 Ericsson
 *
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
    .module('horizon.app.core.trunks')
    .factory('horizon.app.core.trunks.actions.delete.service', deleteService);

  deleteService.$inject = [
    '$q',
    '$location',
    'horizon.app.core.openstack-service-api.neutron',
    'horizon.app.core.openstack-service-api.policy',
    'horizon.app.core.trunks.resourceType',
    'horizon.framework.util.actions.action-result.service',
    'horizon.framework.widgets.modal.deleteModalService'
  ];

  function deleteService(
    $q,
    $location,
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
          ['network', 'delete_trunk']
        ]}
      );
    }

    function perform(items, scope) {
      var trunks = angular.isArray(items) ? items : [items];

      return openModal().then(onComplete);

      function openModal() {
        return deleteModal.open(
          scope,
          trunks,
          {
            labels: labelize(trunks.length),
            deleteEntity: neutron.deleteTrunk
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

        var path = "admin/trunks";
        if ($location.url().indexOf("admin") === -1) {
          path = "project/trunks";
        }
        if ($location.url() !== path && actionResult.result.failed.length === 0 &&
            actionResult.result.deleted.length > 0) {
          $location.path(path);
        } else {
          return actionResult.result;
        }
      }
    }

    function labelize(count) {
      return {
        title: ngettext(
          'Confirm Delete Trunk',
          'Confirm Delete Trunks',
          count),

        message: ngettext(
          'You have selected "%s". Deleted Trunk is not recoverable.',
          'You have selected "%s". Deleted Trunks are not recoverable.',
          count),

        submit: ngettext(
          'Delete Trunk',
          'Delete Trunks',
          count),

        success: ngettext(
          'Deleted Trunk: %s.',
          'Deleted Trunks: %s.',
          count),

        error: ngettext(
          'Unable to delete Trunk: %s.',
          'Unable to delete Trunks: %s.',
          count)
      };
    }

  }

})();
