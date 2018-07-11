/**
 * Copyright 2016 IBM Corp.
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
    .module('horizon.dashboard.identity.roles')
    .factory('horizon.dashboard.identity.roles.actions.edit.service', editService);

  editService.$inject = [
    '$q',
    'horizon.dashboard.identity.roles.basePath',
    'horizon.dashboard.identity.roles.resourceType',
    'horizon.dashboard.identity.roles.role-schema',
    'horizon.app.core.openstack-service-api.keystone',
    'horizon.app.core.openstack-service-api.policy',
    'horizon.framework.widgets.form.ModalFormService',
    'horizon.framework.util.actions.action-result.service',
    'horizon.framework.widgets.toast.service'
  ];

  /**
   * @ngDoc factory
   * @name horizon.dashboard.identity.roles.actions.edit.service
   * @Description A service to handle the Edit Role modal.
   */
  function editService(
    $q,
    basePath,
    resourceType,
    schema,
    keystoneAPI,
    policy,
    modalFormService,
    actionResultService,
    toast
  ) {
    var service = {
      allowed: allowed,
      perform: perform,
      onLoad: onLoad,
      submit: submit,
      onSuccess: onSuccess
    };

    return service;

    //////////////

    function allowed() {
      return $q.all([
        keystoneAPI.canEditIdentity('role'),
        policy.ifAllowed({ rules: [['identity', 'identity:update_role']] })
      ]);
    }

    function perform(role) {
      return keystoneAPI.getRole(role.id).then(service.onLoad);
    }

    function onLoad(response) {
      var config = {
        title: gettext('Edit Role'),
        schema: schema,
        form: ['*'],
        model: response.data,
        size: 'md'
      };
      return modalFormService.open(config).then(service.submit);
    }

    function submit(context) {
      return keystoneAPI.editRole(context.model).then(service.onSuccess);
    }

    function onSuccess(response) {
      toast.add('success', gettext('Role updated successfully.'));

      return actionResultService.getActionResult()
        .updated(resourceType, response.config.data.id)
        .result;
    }
  }
})();
