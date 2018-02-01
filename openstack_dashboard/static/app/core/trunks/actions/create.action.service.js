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
    // Using horizon.framework.widgets.form.ModalFormService and
    // angular-schema-form would have made many things easier, but it wasn't
    // really an option because it does not have a transfer-table widget.
    'horizon.framework.widgets.modal.wizard-modal.service',
    'horizon.framework.widgets.toast.service',
    '$location'
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
    wizardModalService,
    toast,
    $location
  ) {
    var service = {
      perform: perform,
      allowed: allowed
    };

    return service;

    ////////////

    function allowed() {
      // NOTE(lajos katona): in case of admin let's disable create action.
      // TODO(lajos katona): make possible to create/edit from admin panel
      var fromNonAdminUrl = ($location.url().indexOf('admin') === -1);
      var deferred = $q.defer();

      policy.ifAllowed(
        {rules: [
          ['network', 'create_trunk']
        ]}
      ).then(function(result) {
        if (fromNonAdminUrl) {
          deferred.resolve(result);
        } else {
          deferred.reject();
        }
      });

      return deferred.promise;
    }

    function perform() {
      // NOTE(bence romsics): The parent and subport selector steps are shared
      // by the create and edit workflows, therefore we have to initialize the
      // trunk adequately in both cases. That is an empty trunk for create and
      // the trunk to be updated for edit.
      var trunk = {
        admin_state_up: true,
        description: '',
        name: '',
        port_id: undefined,
        sub_ports: []
      };
      return wizardModalService.modal({
        workflow: createWorkflow,
        submit: submit,
        data: {
          initTrunk: trunk,
          getTrunk: $q.when(trunk),
          getPortsWithNets: $q.all({
            getNetworks: neutron.getNetworks(),
            getPorts: userSession.get().then(function(session) {
              return neutron.getPorts({project_id: session.project_id});
            })
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
