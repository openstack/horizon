/*
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *    http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

(function() {
  'use strict';

  angular
    .module('horizon.app.core.server_groups')
    .factory('horizon.app.core.server_groups.actions.create.service', createService);

  createService.$inject = [
    'horizon.app.core.openstack-service-api.nova',
    'horizon.app.core.openstack-service-api.policy',
    'horizon.app.core.server_groups.actions.workflow.service',
    'horizon.app.core.server_groups.resourceType',
    'horizon.framework.widgets.form.ModalFormService',
    'horizon.framework.widgets.toast.service',
    'horizon.framework.util.actions.action-result.service',
    'horizon.framework.util.i18n.gettext'
  ];

  /**
   * @ngDoc factory
   * @name horizon.app.core.server_groups.actions.create.service
   * @Description A service to handle the Create Server Group modal.
   */
  function createService(
    novaAPI,
    policy,
    workflow,
    resourceType,
    modalFormService,
    toast,
    actionResultService,
    gettext
  ) {

    var service = {
      allowed: allowed,
      perform: perform,
      submit: submit
    };

    return service;

    //////////////

    function allowed() {
      return policy.ifAllowed(
        {rules: [['compute', 'os_compute_api:os-server-groups:create']]});
    }

    function perform() {
      var config = workflow.init();
      config.title = gettext("Create Server Group");
      return modalFormService.open(config).then(submit);
    }

    function submit(context) {
      var data = {name: context.model.name};
      // Nova limits only one policy associated with a server group.
      data.policies = [context.model.policy];
      return novaAPI.createServerGroup(data).then(onSuccess);
    }

    function onSuccess(response) {
      var servergroup = response.data;
      toast.add('success', interpolate(
        gettext('Server Group %s was successfully created.'), [servergroup.name]));

      return actionResultService.getActionResult()
        .created(resourceType, servergroup.id)
        .result;
    }

  }
})();
