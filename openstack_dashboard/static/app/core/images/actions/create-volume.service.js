/**
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
    .module('horizon.app.core.images')
    .factory('horizon.app.core.images.actions.create-volume.service', createVolumeService);

  createVolumeService.$inject = [
    '$q',
    'horizon.app.core.openstack-service-api.cinder',
    'horizon.app.core.openstack-service-api.policy',
    'horizon.app.core.openstack-service-api.serviceCatalog',
    'horizon.app.core.images.events',
    'horizon.app.core.images.non_bootable_image_types',
    'horizon.app.core.images.workflows.create-volume.service',
    'horizon.framework.util.actions.action-result.service',
    'horizon.framework.util.q.extensions',
    'horizon.framework.widgets.modal.wizard-modal.service',
    'horizon.framework.widgets.toast.service',
    'horizon.app.core.volumes.resourceType'
  ];

  /*
   * @ngdoc factory
   * @name horizon.app.core.images.actions.create-volume.service
   *
   * @Description
   * Brings up the Create Volume modal.
   */
  function createVolumeService(
    $q,
    cinder,
    policy,
    serviceCatalog,
    events,
    nonBootableImageTypes,
    createVolumeWorkflowService,
    actionResultService,
    $qExtensions,
    wizardModalService,
    toast,
    volumeResourceType
  ) {
    var createVolumePromise, volumeServiceEnabledPromise;

    var message = {
      info: gettext('Creating volume %s')
    };

    var service = {
      initAction: initAction,
      allowed: allowed,
      perform: perform
    };

    return service;

    function initAction() {
      createVolumePromise = policy.ifAllowed({rules: [['volume', 'volume:create']]});
      if (serviceCatalog.ifTypeEnabled('volumev2') ||
          serviceCatalog.ifTypeEnabled('volumev3')) {
        volumeServiceEnabledPromise = true;
      } else {
        volumeServiceEnabledPromise = false;
      }
    }

    function allowed(image) {
      return $q.all([
        imageBootable(image),
        createVolumePromise,
        volumeServiceEnabledPromise,
        imageActive(image)
      ]);
    }

    function perform(image) {
      return wizardModalService.modal({
        data: {image: image},
        workflow: createVolumeWorkflowService,
        submit: submit
      }).result;
    }

    function submit(stepModels) {
      return cinder.createVolume(stepModels.volumeForm).then(showSuccessMessage);
    }

    function showSuccessMessage(response) {
      var volume = response.data;
      toast.add('info', interpolate(message.info, [volume.name]));

      // To make the result of this action generically useful, reformat the return
      // from the deleteModal into a standard form
      return actionResultService.getActionResult()
        .created(volumeResourceType, volume.id)
        .result;
    }

    function imageBootable(image) {
      return $qExtensions.booleanAsPromise(
        nonBootableImageTypes.indexOf(image.container_format) < 0
      );
    }

    function imageActive(image) {
      return $qExtensions.booleanAsPromise(image.status === 'active');
    }
  }
})();
