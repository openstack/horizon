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
    .module('horizon.dashboard.identity.roles')
    .factory('horizon.dashboard.identity.roles.actions.create.service', createService);

  createService.$inject = [
    '$q',
    'horizon.dashboard.identity.roles.basePath',
    'horizon.dashboard.identity.roles.resourceType',
    'horizon.dashboard.identity.roles.role-schema',
    'horizon.app.core.openstack-service-api.keystone',
    'horizon.app.core.openstack-service-api.policy',
    'horizon.framework.widgets.form.ModalFormService',
    'horizon.framework.util.actions.action-result.service',
    'horizon.framework.util.i18n.gettext',
    'horizon.framework.widgets.toast.service'
  ];

  /**
   * @ngDoc factory
   * @name horizon.dashboard.identity.roles.actions.create.service
   * @Description A service to handle the Create Role modal.
   */
  function createService(
    $q,
    basePath,
    resourceType,
    schema,
    keystoneAPI,
    policy,
    modalFormService,
    actionResultService,
    gettext,
    toast
  ) {
    var invalidMsg = gettext("Role already exists.");
    var roles = [];
    var form = [
      {
        key: "name",
        validationMessage: {
          rolesExists: invalidMsg
        },
        $validators: {
          rolesExists: function (name) {
            return (roles.indexOf(name) === -1);
          }
        }
      }
    ];
    var service = {
      allowed: allowed,
      perform: perform,
      submit: submit
    };

    return service;

    //////////////

    function allowed() {
      return $q.all([
        keystoneAPI.canEditIdentity('role'),
        policy.ifAllowed({ rules: [['identity', 'identity:create_role']] })
      ]);
    }

    function perform() {
      getRoles();
      var model = {};

      var config = {
        title: gettext('Create Role'),
        schema: schema,
        form: form,
        model: model,
        size: 'md'
      };
      return modalFormService.open(config).then(submit);
    }

    function submit(context) {
      return keystoneAPI.createRole({name: context.model.name}).then(onSuccess);
    }

    function onSuccess(response) {
      var role = response.data;
      toast.add('success', interpolate(
        gettext('Role %s was successfully created.'), [role.name]));

      return actionResultService.getActionResult()
        .created(resourceType, role.id)
        .result;
    }

    function getRoles() {
      keystoneAPI.getRoles().then(function(response) {
        roles = response.data.items.map(getName);
      });
    }

    function getName(item) {
      return item.name;
    }

  }
})();

