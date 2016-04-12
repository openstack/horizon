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
    .module('horizon.app.core.instances')
    .factory('horizon.app.core.instances.actions.start.service', factory);

  factory.$inject = [
    '$q',
    'horizon.app.core.openstack-service-api.nova',
    'horizon.app.core.openstack-service-api.userSession',
    'horizon.app.core.openstack-service-api.policy',
    'horizon.framework.util.i18n.gettext',
    'horizon.framework.util.q.extensions',
    'horizon.framework.widgets.modal.deleteModalService',
    'horizon.framework.widgets.modal-wait-spinner.service',
    'horizon.framework.widgets.toast.service',
    'horizon.app.core.instances.resourceType'
  ];

  /**
   * @ngDoc factory
   * @name horizon.app.core.instances.actions.delete-instance.service
   *
   * @Description
   * Brings up the delete instance confirmation modal dialog.

   * On submit, delete given instances.
   * On cancel, do nothing.
   */
  function factory(
    $q,
    nova,
    userSessionService,
    policy,
    gettext,
    $qExtensions,
    deleteModal,
    waitSpinner,
    toast,
    instanceResourceType
  ) {
    var scope, context, policyPromise;
    var notAllowedMessage = gettext("You are not allowed to start instances: %s");

    var service = {
      initScope: initScope,
      allowed: allowed,
      perform: perform
    };

    return service;

    //////////////

    function initScope(newScope) {
      scope = newScope;
      context = { };
      policyPromise = policy.ifAllowed({rules: [['instance', 'start_instance']]});
    }

    function perform(item) {
      return nova.startServer(item.id).then(onSuccess);

      function onSuccess() {
        return {
          updated: [{type: instanceResourceType, id: item.id}],
          deleted: [],
          created: [],
          deleted: []
        };
      }
    }


    function allowed(instance) {
      // only row actions pass in instance
      // otherwise, assume it is a batch action
      if (instance) {
        return $q.all([
          notProtected(instance),
          policyPromise,
          userSessionService.isCurrentProject(instance.owner),
          notDeleted(instance)
          // TODO: only valid states are ACTIVE or ERROR
        ]);
      }
      else {
        return policy.ifAllowed({ rules: [['instance', 'start_instance']] });
      }
    }

    function checkPermission(instance) {
      return {promise: allowed(instance), context: instance};
    }

    function createResult(deleteModalResult) {
      // To make the result of this action generically useful, reformat the return
      // from the deleteModal into a standard form
      waitSpinner.hideModalSpinner();
      return {
        created: [],
        updated: [],
        deleted: deleteModalResult.pass.map( mapModalResult ),
        failed: deleteModalResult.fail.map( mapModalResult )
      };
    }

    function onCancel() {
      waitSpinner.hideModalSpinner();
    }
    function notDeleted(instance) {
      return $qExtensions.booleanAsPromise(instance.status !== 'deleted');
    }

    function notProtected(instance) {
      return $qExtensions.booleanAsPromise(!instance.protected);
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
