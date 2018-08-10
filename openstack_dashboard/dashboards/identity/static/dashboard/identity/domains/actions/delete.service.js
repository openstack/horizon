/*
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
    .module('horizon.dashboard.identity.domains.actions')
    .factory('horizon.dashboard.identity.domains.actions.delete.service', deleteService);

  deleteService.$inject = [
    '$q',
    '$location',
    'horizon.app.core.openstack-service-api.keystone',
    'horizon.app.core.openstack-service-api.policy',
    'horizon.dashboard.identity.domains.resourceType',
    'horizon.framework.util.actions.action-result.service',
    'horizon.framework.util.q.extensions',
    'horizon.framework.widgets.modal.deleteModalService',
    'horizon.framework.widgets.toast.service'
  ];

  /*
   * @ngdoc factory
   * @name horizon.dashboard.identity.domains.actions.delete.service
   *
   * @Description
   * Brings up the delete domains confirmation modal dialog.

   * On submit, delete given domains.
   * On cancel, do nothing.
   */
  function deleteService(
    $q,
    $location,
    keystone,
    policy,
    domainsResourceType,
    actionResultService,
    $qExtensions,
    deleteModal,
    toast
  ) {
    var service = {
      allowed: allowed,
      perform: perform
    };

    return service;

    //////////////

    function perform(items, scope) {
      var domains = angular.isArray(items) ? items : [items];
      var context = {
        labels: labelize(domains.length),
        deleteEntity: deleteDomain
      };
      return $qExtensions.allSettled(domains.map(checkPermission)).then(afterCheck);

      function checkPermission(domain) {
        return {promise: allowed(), context: domain};
      }

      function afterCheck(result) {
        var outcome = $q.reject();
        if (result.fail.length > 0) {
          var notAllowedMessage = gettext("You are not allowed to delete domains: %s");
          toast.add('error', getMessage(notAllowedMessage, result.fail));
          outcome = $q.reject(result.fail);
        }
        if (result.pass.length > 0) {
          outcome = deleteModal.open(scope, result.pass.map(getEntity), context).then(createResult);
        }
        return outcome;
      }
    }

    function allowed() {
      return $q.all([
        keystone.canEditIdentity('domain'),
        policy.ifAllowed({ rules: [['identity', 'delete_domain']] })
      ]);
    }

    function createResult(deleteModalResult) {
      var result = actionResultService.getActionResult();
      deleteModalResult.pass.forEach(function markDeleted(item) {
        result.deleted(domainsResourceType, getEntity(item).id);
      });
      deleteModalResult.fail.forEach(function markFailed(item) {
        result.failed(domainsResourceType, getEntity(item).id);
      });
      if (result.result.failed.length === 0 && result.result.deleted.length > 0) {
        $location.path('/identity/domains');
      } else {
        return result.result;
      }
    }

    function labelize(count) {
      return {

        title: ngettext(
          'Confirm Delete Domain',
          'Confirm Delete Domains', count),

        message: ngettext(
          'You have selected "%s". Deleted domain is not recoverable.',
          'You have selected "%s". Deleted domains are not recoverable.', count),

        submit: ngettext(
          'Delete Domain',
          'Delete Domains', count),

        success: ngettext(
          'Deleted domain: %s.',
          'Deleted domains: %s.', count),

        error: ngettext(
          'Unable to delete domain: %s.',
          'Unable to delete domains: %s.', count)
      };
    }

    function deleteDomain(domain) {
      return keystone.deleteDomain(domain);
    }

    function getMessage(message, entities) {
      return interpolate(message, [entities.map(getName).join(", ")]);
    }

    function getName(result) {
      return getEntity(result).name;
    }

    function getEntity(result) {
      return result.context;
    }
  }
})();
