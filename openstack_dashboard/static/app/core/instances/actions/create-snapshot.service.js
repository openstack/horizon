/**
 *
 * (c) Copyright 2016 Hewlett Packard Enterprise Development Company LP
 *
 * Licensed under the Apache License, Version 2.0 (the "License"); you may
 * not use self file except in compliance with the License. You may obtain
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
    .module('horizon.app.core.instances.actions')
    .factory('horizon.app.core.instances.actions.create-snapshot.service', createSnapshotService);

  createSnapshotService.$inject = [
    '$modal',
    '$q',
    'horizon.app.core.basePath',
    'horizon.app.core.images.resourceType',
    'horizon.app.core.openstack-service-api.nova',
    'horizon.app.core.openstack-service-api.policy',
    'horizon.app.core.openstack-service-api.serviceCatalog',
    'horizon.framework.util.q.extensions',
    'horizon.framework.widgets.toast.service',
    'horizon.framework.widgets.modal-wait-spinner.service',
  ];

  /**
   * @ngDoc factory
   * @name horizon.app.core.images.actions.create-volume.service
   *
   * @Description
   * Brings up the Create Instance snapshot modal.
   */
  function createSnapshotService(
    $modal,
    $q,
    basePath,
    imageResourceType,
    nova,
    policy,
    serviceCatalog,
    $qExtensions,
    toast,
    waitSpinner
  ) {
    var scope, createSnapshotPolicy, computeServiceEnabled;
    var SNAPSHOT_READY_STATES = ["ACTIVE", "SHUTOFF", "PAUSED", "SUSPENDED"];
    var newSnapshotName = undefined;
    var message = {
      success: gettext('Snapshot %s was successfully created.')
    };

    var service = {
      initScope: initScope,
      allowed: allowed,
      perform: perform
    };

    return service;

    /////////////////

    function initScope(newScope) {
      scope = newScope;
      createSnapshotPolicy = policy.ifAllowed({rules: [['compute', 'compute:snapshot']]});
      computeServiceEnabled = serviceCatalog.ifTypeEnabled('compute');
    }

    function allowed(instance) {
      return $q.all([
        createSnapshotPolicy,
        computeServiceEnabled,
        instanceSnapshotReady(instance),
        instanceNotDeleting(instance)
      ]);
    }

    function perform(instance) {
      var modalParams = {
        controller: 'horizon.app.core.instances.actions.FormModalController as ctrl',
        templateUrl: basePath + 'instances/actions/form-modal.html',
        resolve: {
          context: function() {
            return {
              title: gettext("Create Instance Snapshot"),
              cancel: gettext("Cancel"),
              submit: gettext("Submit"),
              templateUrl: basePath + 'instances/actions/create-snapshot.html',
              snapshot: {
                name: undefined,
                instance_id: instance.id
              }
            };
          }
        }
      };

      return $modal.open(modalParams).result.then(onSubmit, onCancel);
    }

    function onSubmit(context) {
      var snapshot = context.snapshot;
      newSnapshotName = snapshot.name;
      waitSpinner.showModalSpinner(gettext('Creating Snapshot'));
      return nova.createServerSnapshot(context.snapshot).then(onSuccess);
    }

    function onCancel(response) {
      waitSpinner.hideModalSpinner();
    }

    function onSuccess(response) {
      waitSpinner.hideModalSpinner();
      var snapshot_id = response.data;
      toast.add('success', interpolate(message.success, [newSnapshotName]));

      // To make the result of this action generically useful, reformat the return
      // from the deleteModal into a standard form
      return {
        created: [{type: imageResourceType, id: snapshot_id}],
        updated: [],
        deleted: [],
        failed: []
      };
    }

    function instanceSnapshotReady(instance) {
      return $qExtensions.booleanAsPromise(
        SNAPSHOT_READY_STATES.indexOf(instance.status) >= 0);
    }

    function instanceNotDeleting(instance) {
      var result, task_state;
      task_state = instance["OS-EXT-STS:task_state"];
      if (!task_state) {
        result = true;
      } else {
        result = task_state.toLowerCase() != "deleting";
      }
      return $qExtensions.booleanAsPromise(result);
    }
  }
})();
