/**
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
    .module('horizon.dashboard.identity.users')
    .factory('horizon.dashboard.identity.users.actions.enable.service', enableService);

  enableService.$inject = [
    '$q',
    'horizon.dashboard.identity.users.resourceType',
    'horizon.app.core.openstack-service-api.keystone',
    'horizon.app.core.openstack-service-api.policy',
    'horizon.framework.util.actions.action-result.service',
    'horizon.framework.util.q.extensions',
    'horizon.framework.widgets.toast.service'
  ];

  /**
   * @ngDoc factory
   * @name horizon.dashboard.identity.users.actions.enable.service
   * @Description A service to enable the user.
   */
  function enableService(
    $q,
    resourceType,
    keystone,
    policy,
    actionResultService,
    $qExtensions,
    toast
  ) {
    var message = {
      success: gettext('User %s was successfully enabled.')
    };

    var service = {
      allowed: allowed,
      perform: perform
    };

    return service;

    //////////////

    function allowed(selected) {
      return $q.all([
        keystone.canEditIdentity('user'),
        $qExtensions.booleanAsPromise(!selected.enabled),
        policy.ifAllowed({ rules: [['identity', 'identity:update_user']] })
      ]);
    }

    function perform(selected) {
      return keystone.editUser({id: selected.id, enabled: true}).then(success);
      function success() {
        toast.add('success', interpolate(message.success, [selected.name]));
        return actionResultService.getActionResult()
          .updated(resourceType, selected.id)
          .result;
      }
    }
  }
})();
