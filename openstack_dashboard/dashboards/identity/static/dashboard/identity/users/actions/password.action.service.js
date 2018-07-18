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
    .factory('horizon.dashboard.identity.users.actions.password.service', passwordService);

  passwordService.$inject = [
    '$q',
    'horizon.dashboard.identity.users.resourceType',
    'horizon.dashboard.identity.users.actions.basePath',
    'horizon.dashboard.identity.users.actions.workflow.service',
    'horizon.app.core.openstack-service-api.keystone',
    'horizon.app.core.openstack-service-api.policy',
    'horizon.app.core.openstack-service-api.settings',
    'horizon.framework.util.actions.action-result.service',
    'horizon.framework.widgets.form.ModalFormService',
    'horizon.framework.widgets.toast.service'
  ];

  /**
   * @ngDoc factory
   * @name horizon.dashboard.identity.users.actions.password.service
   * @Description A service to change the user password.
   */
  function passwordService(
    $q,
    resourceType,
    basePath,
    workflow,
    keystone,
    policy,
    settings,
    actionResultService,
    modal,
    toast
  ) {
    var message = {
      success: gettext('User password has been updated successfully.')
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

    // eslint-disable-next-line no-unused-vars
    function perform(selected, scope, errorCode) {
      return settings.getSetting('ENFORCE_PASSWORD_CHECK', false).then(function (response) {
        var adminPassword = response;
        return keystone.getUser(selected.id).then(function (response) {
          var config = workflow.init("password", adminPassword, errorCode);
          config.title = gettext("Change Password");
          config.model = {};
          config.model.id = response.data.id;
          config.model.domain_name = response.data.domain_name;
          config.model.domain_id = response.data.domain_id;
          config.model.name = response.data.name;
          return modal.open(config).then(submit);
        });
      });
    }

    function submit(context) {
      delete context.model.domain_name;
      delete context.model.domain_id;
      delete context.model.enabled;
      return keystone.editUser(context.model).then(success, error);

      function success() {
        toast.add('success', message.success);
        return actionResultService.getActionResult()
          .updated(resourceType, context.model.id)
          .result;
      }

      function error(response) {
        if (response.status === 400) {
          perform(context.model, null, response.data);
        } else {
          return actionResultService.getActionResult()
            .updated(resourceType, context.model.id)
            .result;
        }
      }
    }
  }
})();
