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
    .factory('horizon.dashboard.identity.users.actions.update.service', updateService);

  updateService.$inject = [
    '$q',
    'horizon.dashboard.identity.users.resourceType',
    'horizon.dashboard.identity.users.actions.basePath',
    'horizon.dashboard.identity.users.actions.workflow.service',
    'horizon.app.core.openstack-service-api.keystone',
    'horizon.app.core.openstack-service-api.policy',
    'horizon.framework.util.actions.action-result.service',
    'horizon.framework.widgets.form.ModalFormService',
    'horizon.framework.widgets.toast.service'
  ];

  /**
   * @ngDoc factory
   * @name horizon.dashboard.identity.users.actions.update.service
   * @Description A service to edit the user details.
   */
  function updateService(
    $q,
    resourceType,
    basePath,
    workflow,
    keystone,
    policy,
    actionResultService,
    modal,
    toast
  ) {
    var message = {
      success: gettext('User %s was successfully updated.')
    };

    return {
      allowed: allowed,
      perform: perform,
      submit: submit
    };

    //////////////

    function allowed() {
      return $q.all([
        keystone.canEditIdentity('user'),
        policy.ifAllowed({ rules: [['identity', 'identity:update_user']] })
      ]);
    }

    function perform(selected) {
      return keystone.getUser(selected.id).then(function (response) {
        var config = workflow.init("update");
        config.title = gettext("Edit User");
        config.model = {};
        config.model.id = response.data.id;
        config.model.domain_name = response.data.domain_name;
        config.model.domain_id = response.data.domain_id;
        config.model.name = response.data.name;
        config.model.email = response.data.email;
        config.model.description = response.data.description;
        config.model.project = response.data.default_project_id;
        return modal.open(config).then(submit);
      });
    }

    function submit(context) {
      delete context.model.domain_name;
      delete context.model.domain_id;
      delete context.model.enabled;
      return keystone.editUser(context.model).then(success);

      function success() {
        toast.add('success', interpolate(message.success, [context.model.name]));
        return actionResultService.getActionResult()
          .updated(resourceType, context.model.id)
          .result;
      }
    }
  }
})();
