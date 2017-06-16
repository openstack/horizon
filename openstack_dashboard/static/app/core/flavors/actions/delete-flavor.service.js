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
    .module('horizon.app.core.flavors')
    .factory('horizon.app.core.flavors.actions.delete-flavor.service', deleteFlavorService);

  deleteFlavorService.$inject = [
    'horizon.app.core.openstack-service-api.nova',
    'horizon.framework.util.actions.action-result.service',
    'horizon.framework.util.i18n.gettext',
    'horizon.framework.util.q.extensions',
    'horizon.framework.widgets.modal.deleteModalService',
    'horizon.app.core.flavors.resourceType'
  ];

  /*
   * @ngdoc factory
   * @name horizon.app.core.flavors.actions.delete-flavor.service
   *
   * @Description
   * Brings up the delete flavors confirmation modal dialog.

   * On submit, delete given flavors.
   * On cancel, do nothing.
   */
  function deleteFlavorService(
    nova,
    actionResultService,
    gettext,
    $qExtensions,
    deleteModal,
    flavorsResourceType
  ) {

    var service = {
      allowed: allowed,
      perform: perform
    };

    return service;

    //////////////

    function allowed() {
      return $qExtensions.booleanAsPromise(true);
    }

    function perform(items, scope) {
      var flavors = angular.isArray(items) ? items : [items];
      var context = {
        labels: labelize(flavors.length),
        deleteEntity: deleteFlavor
      };
      return deleteModal.open(scope, flavors, context).then(deleteResult);
    }

    function deleteResult(deleteModalResult) {
      // To make the result of this action generically useful, reformat the return
      // from the deleteModal into a standard form
      var actionResult = actionResultService.getActionResult();
      deleteModalResult.pass.forEach(function markDeleted(item) {
        actionResult.deleted(flavorsResourceType, item.context.id);
      });
      deleteModalResult.fail.forEach(function markFailed(item) {
        actionResult.failed(flavorsResourceType, item.context.id);
      });
      return actionResult.result;
    }

    function labelize(count) {
      return {

        title: ngettext(
          'Confirm Delete Flavor',
          'Confirm Delete Flavors', count),

        message: ngettext(
          'You have selected "%s". Deleted flavor is not recoverable.',
          'You have selected "%s". Deleted flavors are not recoverable.', count),

        submit: ngettext(
          'Delete Flavor',
          'Delete Flavors', count),

        success: ngettext(
          'Deleted Flavor: %s.',
          'Deleted Flavors: %s.', count),

        error: ngettext(
          'Unable to delete Flavor: %s.',
          'Unable to delete Flavors: %s.', count)
      };
    }

    function deleteFlavor(flavor) {
      return nova.deleteFlavor(flavor, true);
    }
  }
})();
