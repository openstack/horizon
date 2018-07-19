/**
 * Copyright 2017 99Cloud
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
    .module('horizon.dashboard.identity.groups')
    .factory('horizon.dashboard.identity.groups.actions.create.service', createService);

  createService.$inject = [
    '$q',
    'horizon.dashboard.identity.groups.resourceType',
    'horizon.app.core.openstack-service-api.keystone',
    'horizon.app.core.openstack-service-api.policy',
    'horizon.framework.widgets.form.ModalFormService',
    'horizon.framework.util.actions.action-result.service',
    'horizon.framework.util.i18n.gettext',
    'horizon.framework.widgets.toast.service'
  ];

  /**
   * @ngDoc factory
   * @name horizon.dashboard.identity.groups.actions.create.service
   * @Description A service to handle the Create Group modal.
   */
  function createService(
    $q,
    resourceType,
    keystoneAPI,
    policy,
    modalFormService,
    actionResultService,
    gettext,
    toast
  ) {
    var service = {
      allowed: allowed,
      perform: perform,
      submit: submit
    };

    return service;

    //////////////

    function allowed() {
      return $q.all([
        keystoneAPI.canEditIdentity('group'),
        policy.ifAllowed({ rules: [['identity', 'identity:create_group']] })
      ]);
    }

    function perform() {
      var model = {
        name: '',
        description: ''
      };

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
        title: gettext('Create Group'),
        schema: schema,
        form: ['*'],
        model: model
      };
      return modalFormService.open(config).then(submit);
    }

    function submit(context) {
      return keystoneAPI.createGroup(context.model).then(onSuccess);
    }

    function onSuccess(response) {
      var group = response.data;
      toast.add('success', interpolate(
        gettext('Group %s was successfully created.'), [group.name]));

      return actionResultService.getActionResult()
        .created(resourceType, group.id)
        .result;
    }

  }
})();

