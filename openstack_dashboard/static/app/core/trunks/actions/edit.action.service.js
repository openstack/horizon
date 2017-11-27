/*
 * Copyright 2017 Ericsson
 *
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
    .module('horizon.app.core.trunks')
    .factory('horizon.app.core.trunks.actions.edit.service', editService);

  editService.$inject = [
    '$q',
    '$location',
    'horizon.app.core.openstack-service-api.neutron',
    'horizon.app.core.openstack-service-api.policy',
    'horizon.app.core.openstack-service-api.userSession',
    'horizon.app.core.trunks.actions.editWorkflow',
    'horizon.app.core.trunks.actions.ports-extra.service',
    'horizon.app.core.trunks.resourceType',
    'horizon.framework.util.actions.action-result.service',
    'horizon.framework.widgets.modal.wizard-modal.service',
    'horizon.framework.widgets.toast.service'
  ];

  /**
   * @ngDoc factory
   * @name horizon.app.core.trunks.actions.editService
   * @Description A service to handle the Edit Trunk modal.
   */
  function editService(
    $q,
    $location,
    neutron,
    policy,
    userSession,
    editWorkflow,
    portsExtra,
    resourceType,
    actionResultService,
    wizardModalService,
    toast
  ) {
    var service = {
      perform: perform,
      allowed: allowed
    };
    return service;

    ////////////

    function allowed() {
      return policy.ifAllowed(
        {rules: [
          ['network', 'add_subports'],
          ['network', 'remove_subports']
        ]}
      );
    }

    function perform(selected) {
      var params = {};

      if ($location.url().indexOf('admin') === -1) {
        params = {project_id: userSession.project_id};
      }

      return wizardModalService.modal({
        workflow: editWorkflow,
        submit: submit,
        data: {
          // The step controllers can and will freshly query the trunk
          // by using the getTrunk promise below. For all updateable
          // attributes you should use that. But to make our lives a bit
          // easier we also pass synchronously (and redundantly) the trunk
          // we queried earlier. Remember to only use those attributes
          // of it that are not allowed to be updated.
          initTrunk: selected,
          getTrunk: neutron.getTrunk(selected.id).then(function(response) {
            return response.data;
          }),
          getPortsWithNets: $q.all({
            getNetworks: neutron.getNetworks(params),
            getPorts: neutron.getPorts(params)
          }).then(function(responses) {
            var networks = responses.getNetworks.data.items;
            var ports = responses.getPorts.data.items;
            return portsExtra.addNetworkAndSubnetInfo(
              ports, networks).sort(portsExtra.cmpPortsByNameAndId);
          })
        }
      }).result;
    }

    function submit(stepModels) {
      // See also at submit() in create action.
      var oldTrunk = stepModels.initTrunk;
      var trunk = angular.copy(oldTrunk);
      var stepName, getTrunkSlice;

      for (stepName in stepModels.trunkSlices) {
        if (stepModels.trunkSlices.hasOwnProperty(stepName)) {
          getTrunkSlice = stepModels.trunkSlices[stepName];
          angular.extend(trunk, getTrunkSlice());
        }
      }
      return neutron.updateTrunk(oldTrunk, trunk).then(onSuccess);

      function onSuccess(response) {
        var trunk = response.data;
        // We show this green toast on a no-op update too, but meh.
        toast.add('success', interpolate(
          gettext('Trunk %s was successfully edited.'), [trunk.name]));
        return actionResultService.getActionResult()
          .updated(resourceType, trunk.id)
          .result;
      }
    }

  }
})();
