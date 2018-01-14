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
    .module('horizon.dashboard.identity.groups')
    .factory('horizon.dashboard.identity.groups.actions.edit.service', editService);

  editService.$inject = [
    '$q',
    'horizon.dashboard.identity.groups.resourceType',
    'horizon.app.core.openstack-service-api.keystone',
    'horizon.app.core.openstack-service-api.policy',
    'horizon.framework.widgets.form.ModalFormService',
    'horizon.framework.util.actions.action-result.service',
    'horizon.framework.widgets.toast.service'
  ];

  /**
   * @ngDoc factory
   * @name horizon.dashboard.identity.groups.actions.edit.service
   * @Description A service to handle the Edit Group modal.
   */
  function editService(
    $q,
    resourceType,
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
        keystoneAPI.canEditIdentity('group'),
        policy.ifAllowed({ rules: [['identity', 'identity:update_group']] })
      ]);
    }

    function perform(group) {
      return keystoneAPI.getGroup(group.id).then(service.onLoad);
    }

    function onLoad(response) {
      var schema = {
        type: 'object',
        properties: {
          name: {
            title: gettext('Name'),
            type: 'string'
          },
          description: {
            title: gettext('Description'),
            type: 'string'
          }
        },
        required: ['name']
      };

      var config = {
        title: gettext('Edit Group'),
        schema: schema,
        form: ['*'],
        model: response.data
      };
      return modalFormService.open(config).then(service.submit);
    }

    function submit(context) {
      return keystoneAPI.editGroup(context.model).then(service.onSuccess);
    }

    function onSuccess(response) {
      toast.add('success', gettext('Group updated successfully.'));

      return actionResultService.getActionResult()
        .updated(resourceType, response.config.data.id)
        .result;
    }
  }
})();
