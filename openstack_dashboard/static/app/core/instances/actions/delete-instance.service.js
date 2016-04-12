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
    .factory('horizon.app.core.instances.actions.delete-instance.service', factory);

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
    var scope, context, deletePromise;
    var notAllowedMessage = gettext("You are not allowed to delete instances: %s");

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
      deletePromise = policy.ifAllowed({rules: [['instance', 'delete_instance']]});
    }

    function perform(items) {
      var instances = angular.isArray(items) ? items : [items];
      context.labels = labelize(instances.length);
      context.deleteEntity = deleteItem;
      return $qExtensions.allSettled(instances.map(checkPermission)).then(afterCheck);
    }

    function allowed(instance) {
      // only row actions pass in instance
      // otherwise, assume it is a batch action
      if (instance) {
        return $q.all([
          notProtected(instance),
          deletePromise,
          userSessionService.isCurrentProject(instance.owner),
          notDeleted(instance)
        ]);
      }
      else {
        return policy.ifAllowed({ rules: [['instance', 'delete_instance']] });
      }
    }

    function checkPermission(instance) {
      return {promise: allowed(instance), context: instance};
    }

    function afterCheck(result) {
      var outcome = $q.reject();  // Reject the promise by default
      if (result.fail.length > 0) {
        toast.add('error', getMessage(notAllowedMessage, result.fail));
        outcome = $q.reject(result.fail);
      }
      if (result.pass.length > 0) {
        outcome = deleteModal.open(scope, result.pass.map(getEntity), context).then(createResult, onCancel);
      }
      waitSpinner.showModalSpinner(ngettext('Deleting Instance', 'Deleting Instance', result.pass.length));
      return outcome;
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

    function mapModalResult(item) {
      return {
        type: instanceResourceType,
        id: getEntity(item).id
      };
    }

    function labelize(count) {
      return {

        title: ngettext(
          'Confirm Delete Instance',
          'Confirm Delete Instances', count),

        message: ngettext(
          'You have selected "%s". Deleted instance is not recoverable.',
          'You have selected "%s". Deleted instances are not recoverable.', count),

        submit: ngettext(
          'Delete Instance',
          'Delete Instances', count),

        success: ngettext(
          'Deleted Instance: %s.',
          'Deleted Instances: %s.', count),

        error: ngettext(
          'Unable to delete Instance: %s.',
          'Unable to delete Instances: %s.', count)
      };
    }

    function notDeleted(instance) {
      return $qExtensions.booleanAsPromise(instance.status !== 'deleted');
    }

    function notProtected(instance) {
      return $qExtensions.booleanAsPromise(!instance.protected);
    }

    function deleteItem(item) {
      return nova.deleteServer(item, true);
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
