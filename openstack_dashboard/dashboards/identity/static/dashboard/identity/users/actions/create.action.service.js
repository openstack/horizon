/**
 * Copyright 2016 99Cloud
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
    .module('horizon.dashboard.identity.users')
    .factory('horizon.dashboard.identity.users.actions.create.service', createService);

  createService.$inject = [
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
   * @name horizon.dashboard.identity.users.actions.create.service
   * @Description A service to open the user wizard.
   */
  function createService(
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
      success: gettext('User %s was successfully created.')
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
        policy.ifAllowed({ rules: [['identity', 'identity:create_user']] })
      ]);
    }

    function perform() {
      var config = workflow.init("create");
      config.title = gettext("Create User");
      return modal.open(config).then(submit);
    }

    function submit(context) {
      return keystone.createUser(context.model).then(success);

      function success(response) {
        var user = response.data;
        toast.add('success', interpolate(message.success, [user.name]));
        // Assign project role for the new user.
        keystone.grantRole(user.default_project_id, context.model.role, user.id);
        return actionResultService.getActionResult()
          .created(resourceType, user.id)
          .result;
      }
    }
  }
})();
