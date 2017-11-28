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
    .factory('horizon.app.core.trunks.actions.create.service', createService);

  createService.$inject = [
    '$q',
    'horizon.app.core.openstack-service-api.neutron',
    'horizon.app.core.openstack-service-api.policy',
    'horizon.app.core.openstack-service-api.userSession',
    'horizon.app.core.trunks.actions.createWorkflow',
    'horizon.app.core.trunks.actions.ports-extra.service',
    'horizon.app.core.trunks.resourceType',
    'horizon.framework.util.actions.action-result.service',
    'horizon.framework.widgets.modal-wait-spinner.service',
    // Using horizon.framework.widgets.form.ModalFormService and
    // angular-schema-form would have made many things easier, but it wasn't
    // really an option because it does not have a transfer-table widget.
    'horizon.framework.widgets.modal.wizard-modal.service',
    'horizon.framework.widgets.toast.service'
  ];

  /**
   * @ngDoc factory
   * @name horizon.app.core.trunks.actions.createService
   * @Description A service to handle the Create Trunk modal.
   */
  function createService(
    $q,
    neutron,
    policy,
    userSession,
    createWorkflow,
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
          ['network', 'create_trunk']
        ]}
      );
    }

    function perform() {
      // NOTE(bence romsics): Suboptimal UX. We delay opening the modal until
      // neutron objects are loaded. But ideally the steps independent of
      // already existing neutron objects (ie. the trunk details step) could
      // already work while loading neutron stuff in the background.
      spinnerService.showModalSpinner(gettext('Please Wait'));

      return $q.all({
        // TODO(bence romsics): Query filters of port and network listings
        // should be aligned. While here it looks like we query all
        // possible ports and all possible networks this is not really the
        // case. A few calls down in openstack_dashboard/api/neutron.py
        // we have a filterless port listing, but networks are listed
        // by network_list_for_tenant() which includes some hardcoded
        // tenant-specific filtering. Therefore here we may get back some
        // ports whose networks we don't have. This is only a problem for
        // admin and even then it means just missing network and subnet
        // metadata on some ports. But anyway when we want this panel to
        // work for admin too, we should fix this.
        getNetworks: neutron.getNetworks(),
        getPorts: userSession.get().then(function(session) {
          return neutron.getPorts({project_id: session.project_id});
        })
      }).then(function(responses) {
        var networks = responses.getNetworks.data.items;
        var ports = responses.getPorts.data.items;
        return {
          parentPortCandidates: portsExtra.addNetworkAndSubnetInfo(
            ports.filter(portsExtra.isParentPortCandidate),
            networks),
          subportCandidates: portsExtra.addNetworkAndSubnetInfo(
            ports.filter(portsExtra.isSubportCandidate),
            networks)
        };
      }).then(openModal);

      function openModal(params) {
        spinnerService.hideModalSpinner();

        return wizardModalService.modal({
          workflow: createWorkflow,
          submit: submit,
          data: {
            initTrunk: {
              admin_state_up: true,
              description: '',
              name: '',
              port_id: undefined,
              sub_ports: []
            },
            ports: {
              parentPortCandidates: params.parentPortCandidates.sort(
                portsExtra.cmpPortsByNameAndId),
              subportCandidates: params.subportCandidates.sort(
                portsExtra.cmpPortsByNameAndId),
              subportsOfInitTrunk: []
            },
            // When both the parent port and subports steps show mostly the
            // same ports available, then a port allocated in one step should
            // become unavailable in the other.
            crossHide: true
          }
        }).result;
      }
    }

    function submit(stepModels) {
      // NOTE(bence romsics): The action should not know about the steps. How
      // many steps we have, or their names. All we have to know is that each
      // has a closure returning a trunk slice and these slices can be merged
      // by extend() to a full trunk model.
      var trunk = {};
      var stepName, getTrunkSlice;

      for (stepName in stepModels.trunkSlices) {
        if (stepModels.trunkSlices.hasOwnProperty(stepName)) {
          getTrunkSlice = stepModels.trunkSlices[stepName];
          angular.extend(trunk, getTrunkSlice());
        }
      }
      return neutron.createTrunk(trunk).then(onSuccess);

      function onSuccess(response) {
        var trunk = response.data;
        toast.add('success', interpolate(
          gettext('Trunk %s was successfully created.'), [trunk.name]));
        return actionResultService.getActionResult()
          .created(resourceType, trunk.id)
          .result;
      }
    }

  }
})();
