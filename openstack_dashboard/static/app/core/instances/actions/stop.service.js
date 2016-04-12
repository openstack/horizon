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
    .factory('horizon.app.core.instances.actions.stop.service', factory);

  factory.$inject = [
    '$q',
    'horizon.app.core.openstack-service-api.nova',
    'horizon.app.core.openstack-service-api.userSession',
    'horizon.app.core.openstack-service-api.policy',
    'horizon.framework.util.i18n.gettext',
    'horizon.framework.util.q.extensions',
    'horizon.framework.widgets.modal-wait-spinner.service',
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
    waitSpinner,
    instanceResourceType
  ) {
    var scope, policyPromise;

    var service = {
      initScope: initScope,
      allowed: allowed,
      perform: perform
    };

    return service;

    //////////////

    function initScope(newScope) {
      scope = newScope;
      policyPromise = policy.ifAllowed({rules: [['instance', 'stop_instance']]});
    }

    function perform(item) {
      waitSpinner.showModalSpinner(gettext('Please Wait'));
      return nova.stopServer(item.id).then(onSuccess, onFailure);

      function onSuccess() {
      waitSpinner.hideModalSpinner();
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
          properState(instance)
        ]);
      }
      else {
        return policy.ifAllowed({ rules: [['instance', 'stop_instance']] });
      }
    }

    function onFailure() {
      waitSpinner.hideModalSpinner();
    }

    function properState(instance) {
      return $qExtensions.booleanAsPromise(instance.status === 'ACTIVE' || instance.status === 'ERROR');
    }

    function notProtected(instance) {
      return $qExtensions.booleanAsPromise(!instance.protected);
    }
  }
})();
