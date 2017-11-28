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
    'horizon.app.core.openstack-service-api.neutron',
    'horizon.app.core.openstack-service-api.policy',
    'horizon.app.core.openstack-service-api.userSession',
    'horizon.app.core.trunks.actions.editWorkflow',
    'horizon.app.core.trunks.actions.ports-extra.service',
    'horizon.app.core.trunks.resourceType',
    'horizon.framework.util.actions.action-result.service',
    'horizon.framework.widgets.modal-wait-spinner.service',
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
    neutron,
    policy,
    userSession,
    editWorkflow,
    portsExtra,
    resourceType,
    actionResultService,
    spinnerService,
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
      // See also at perform() in create action.
      spinnerService.showModalSpinner(gettext('Please Wait'));

      return $q.all({
        getNetworks: neutron.getNetworks(),
        getPorts: userSession.get().then(function(session) {
          return neutron.getPorts({project_id: session.project_id});
        }),
        getTrunk: neutron.getTrunk(selected.id)
      }).then(function(responses) {
        var networks = responses.getNetworks.data.items;
        var ports = responses.getPorts.data.items;
        var trunk = responses.getTrunk.data;
        return {
          subportCandidates: portsExtra.addNetworkAndSubnetInfo(
            ports.filter(portsExtra.isSubportCandidate),
            networks),
          subportsOfInitTrunk: portsExtra.addNetworkAndSubnetInfo(
            ports.filter(portsExtra.isSubportOfTrunk.bind(null, selected.id)),
            networks),
          trunk: trunk
        };
      }).then(openModal);

      function openModal(params) {
        spinnerService.hideModalSpinner();

        return wizardModalService.modal({
          workflow: editWorkflow,
          submit: submit,
          data: {
            initTrunk: params.trunk,
            ports: {
              parentPortCandidates: [],
              subportCandidates: params.subportCandidates.sort(
                portsExtra.cmpPortsByNameAndId),
              subportsOfInitTrunk: params.subportsOfInitTrunk.sort(
                portsExtra.cmpSubportsBySegmentationTypeAndId)
            },
            // There's no point of cross-hiding ports between the parent port
            // and subports steps since the edit workflow cannot have a parent
            // port step.
            crossHide: false
          }
        }).result;
      }
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
