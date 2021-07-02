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

  /**
  * @ngdoc overview
  * @ngname horizon.app.core.network_qos.actions.create.service
  *
  * @description
  * Provides all of the actions for creating network qos policy.
  */

  angular
    .module('horizon.app.core.network_qos')
    .factory('horizon.app.core.network_qos.actions.create.service', createService);

  createService.$inject = [
    'horizon.app.core.openstack-service-api.neutron',
    'horizon.app.core.openstack-service-api.policy',
    'horizon.app.core.network_qos.actions.workflow.service',
    'horizon.app.core.network_qos.resourceType',
    'horizon.framework.widgets.form.ModalFormService',
    'horizon.framework.widgets.toast.service',
    'horizon.framework.util.actions.action-result.service'
  ];

  function createService(
    neutronAPI,
    policy,
    workflow,
    resourceType,
    modalFormService,
    toast,
    actionResultService
  ) {

    var service = {
      allowed: allowed,
      perform: perform,
      submit: submit
    };

    return service;

    //////
    function allowed() {
      return policy.ifAllowed(
        {rules: [
          ['network', 'create_qos_policy']
        ]}
      );
    }

    function perform() {
      var createPolicy = workflow.init();
      createPolicy.title = gettext('Create QoS Policy');
      return modalFormService.open(createPolicy).then(submit);
    }

    function submit(context) {
      var data = {name: context.model.name, description: context.model.description,
              shared: context.model.shared};
      return neutronAPI.createNetworkQoSPolicy(data).then(onCreateNetworkQoSPolicy);
    }

    function onCreateNetworkQoSPolicy(response) {
      var qospolicy = response.data;
      toast.add('success', interpolate(
        gettext('QoS Policy %s was successfully created.'), [qospolicy.name]));

      return actionResultService.getActionResult()
        .created(resourceType, qospolicy.id)
        .result;
    }
  }
})();
