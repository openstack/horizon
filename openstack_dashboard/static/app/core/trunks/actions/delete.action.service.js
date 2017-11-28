/*
 * Copyright 2017 Ericsson
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

  angular
    .module('horizon.app.core.trunks')
    .factory(
      'horizon.app.core.trunks.actions.delete.service',
      deleteTrunkService
    );

  deleteTrunkService.$inject = [
    '$q',
    'horizon.app.core.openstack-service-api.neutron',
    'horizon.app.core.openstack-service-api.userSession',
    'horizon.app.core.openstack-service-api.policy',
    'horizon.framework.util.actions.action-result.service',
    'horizon.framework.util.i18n.gettext',
    'horizon.framework.util.q.extensions',
    'horizon.framework.widgets.modal.deleteModalService',
    'horizon.framework.widgets.toast.service',
    'horizon.app.core.trunks.resourceType'
  ];

  function deleteTrunkService(
    $q,
    neutron,
    userSessionService,
    policy,
    actionResultService,
    gettext,
    $qExtensions,
    deleteModal,
    toast,
    trunkResourceType
  ) {
    var scope, context, deleteTrunkPromise;

    var service = {
      initScope: initScope,
      allowed: allowed,
      perform: perform
    };

    return service;

    function initScope(newScope) {
      scope = newScope;
      context = {};
      deleteTrunkPromise = policy.ifAllowed(
        {rules: [['trunk', 'delete_trunk']]});
    }

    function perform(items) {
      var Trunks = angular.isArray(items) ? items : [items];
      context.labels = labelize(Trunks.length);
      context.deleteEntity = neutron.deleteTrunk;
      return $qExtensions.allSettled(Trunks.map(checkPermission))
        .then(afterCheck);
    }

    function allowed(trunk) {
      if (trunk) {
        return $q.all([
          deleteTrunkPromise,
          userSessionService.isCurrentProject(trunk.project_id)
        ]);
      } else {
        return deleteTrunkPromise;
      }
    }

    function checkPermission(trunk) {
      return {promise: allowed(trunk), context: trunk};
    }

    function afterCheck(result) {
      var outcome = $q.reject();
      if (result.fail.length > 0) {
        var msg = interpolate(
          gettext("You are not allowed to delete trunks: %s"),
          [result.fail.map(function (x) {return x.context.name;}).join(", ")]);
        toast.add('error', msg, result.fail);
        outcome = $q.reject(result.fail);
      }
      if (result.pass.length > 0) {
        outcome = deleteModal.open(
            scope,
            result.pass.map(function (x) {return x.context;}),
            context)
          .then(createResult);
      }
      return outcome;
    }

    function createResult(deleteModalResult) {
      var actionResult = actionResultService.getActionResult();
      deleteModalResult.pass.forEach(function markDeleted(item) {
        actionResult.deleted(trunkResourceType, item.context.id);
      });
      deleteModalResult.fail.forEach(function markFailed(item) {
        actionResult.failed(trunkResourceType, item.context.id);
      });
      return actionResult.result;
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
