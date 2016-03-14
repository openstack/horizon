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
    'horizon.app.core.images.workflows.create-volume.service',
    'horizon.app.core.images.events',
    'horizon.framework.util.q.extensions',
    'horizon.framework.widgets.modal.wizard-modal.service',
    'horizon.framework.widgets.toast.service'
  ];

  /**
   * @ngDoc factory
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
    createVolumeWorkflowService,
    events,
    $qExtensions,
    wizardModalService,
    toast
  ) {
    var scope, createVolumePromise, volumeServiceEnabledPromise;
    var NON_BOOTABLE_IMAGE_TYPES = ['aki', 'ari'];

    var volume = {};

    var message = {
      success: gettext('Volume %s was successfully created.')
    };

    var service = {
      initScope: initScope,
      allowed: allowed,
      perform: perform
    };

    return service;

    function initScope(newScope) {
      scope = newScope;

      var watchVolumeChange = scope.$on(events.VOLUME_CHANGED, onChangedVolume);
      scope.$on('$destroy', destroy);
      createVolumePromise = policy.ifAllowed({rules: [['volume', 'volume:create']]});
      volumeServiceEnabledPromise = serviceCatalog.ifTypeEnabled('volume');

      function destroy() {
        watchVolumeChange();
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
      scope.image = image;
      return wizardModalService.modal({
        scope: scope,
        workflow: createVolumeWorkflowService,
        submit: submit
      }).result;
    }

    function submit() {
      return cinder.createVolume(volume).then(showSuccessMessage);
    }

    function showSuccessMessage(response) {
      var volume = response.data;
      toast.add('success', interpolate(message.success, [volume.name]));
      return {
          // Object intentionally left blank. This data is passed to
          // code that holds this action's promise. In the future, it may
          // contain entity IDs and types that were modified by this action.
      };
    }

    function imageBootable(image) {
      return $qExtensions.booleanAsPromise(
        NON_BOOTABLE_IMAGE_TYPES.indexOf(image.container_format) < 0
      );
    }

    function imageActive(image) {
      return $qExtensions.booleanAsPromise(image.status === 'active');
    }

    //// scope functions ////
    function onChangedVolume(e, newVolume) {
      volume = newVolume;
      e.stopPropagation();
    }

  }
})();
