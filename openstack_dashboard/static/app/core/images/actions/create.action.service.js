/**
 * (c) Copyright 2016 Hewlett-Packard Development Company, L.P.
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
    .module('horizon.app.core.images')
    .factory('horizon.app.core.images.actions.create.service', createService);

  createService.$inject = [
    '$q',
    'horizon.app.core.images.events',
    'horizon.app.core.images.resourceType',
    'horizon.app.core.images.actions.createWorkflow',
    'horizon.app.core.metadata.service',
    'horizon.app.core.openstack-service-api.glance',
    'horizon.app.core.openstack-service-api.policy',
    'horizon.framework.util.actions.action-result.service',
    'horizon.framework.widgets.modal.wizard-modal.service',
    'horizon.framework.widgets.toast.service'
  ];

  /**
   * @ngDoc factory
   * @name horizon.app.core.images.actions.createService
   * @Description A service to open the user wizard.
   */
  function createService(
    $q,
    events,
    resourceType,
    createWorkflow,
    metadataService,
    glance,
    policy,
    actionResultService,
    wizardModalService,
    toast
  ) {
    var message = {
      success: gettext('Image %s was successfully created.')
    };

    var scope;

    var service = {
      perform: perform,
      allowed: allowed
    };

    return service;

    //////////////

    function allowed() {
      return policy.ifAllowed({ rules: [['image', 'add_image']] });
    }

    function perform(selected, $scope) {
      scope = $scope;

      return wizardModalService.modal({
        workflow: createWorkflow,
        submit: submit
      }).result;
    }

    function submit(stepModels) {
      var finalModel = angular.extend(
        {},
        stepModels.imageForm,
        stepModels.updateMetadataForm);
      if (finalModel.source_type === 'url') {
        delete finalModel.data;
      } else {
        delete finalModel.image_url;
      }
      function onProgress(progress) {
        scope.$broadcast(events.IMAGE_UPLOAD_PROGRESS, progress);
      }
      return glance.createImage(finalModel, onProgress).then(onCreateImage);
    }

    function onCreateImage(response) {
      var newImage = response.data;
      toast.add('success', interpolate(message.success, [newImage.name]));
      return actionResultService.getActionResult()
        .created(resourceType, newImage.id)
        .result;
    }

  } // end of createService
})(); // end of IIFE
