/**
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
    'horizon.app.core.images.events',
    'horizon.app.core.images.resourceType',
    'horizon.app.core.images.actions.createWorkflow',
    'horizon.app.core.metadata.service',
    'horizon.app.core.openstack-service-api.glance',
    'horizon.app.core.openstack-service-api.policy',
    'horizon.framework.widgets.modal.wizard-modal.service',
    'horizon.framework.widgets.toast.service'
  ];

  /**
   * @ngDoc factory
   * @name horizon.app.core.images.actions.createService
   * @Description A service to open the user wizard.
   */
  function createService(
    events,
    resourceType,
    createWorkflow,
    metadataService,
    glance,
    policy,
    wizardModalService,
    toast
  ) {
    var message = {
      success: gettext('Image %s was successfully created.'),
      successMetadata: gettext('Image Metadata %s was successfully updated.')
    };

    var model = {
      image: {},
      metadata: {}
    };

    var scope;

    var service = {
      initScope: initScope,
      perform: perform,
      allowed: allowed
    };

    return service;

    //////////////

    // include this function in your service
    // if you plan to emit events to the parent controller
    function initScope($scope) {
      var watchImageChange = $scope.$on(events.IMAGE_CHANGED, onImageChange);
      var watchMetadataChange = $scope.$on(events.IMAGE_METADATA_CHANGED, onMetadataChange);

      scope = $scope;

      $scope.$on('$destroy', destroy);

      function destroy() {
        watchImageChange();
        watchMetadataChange();
      }
    }

    function onImageChange(e, image) {
      model.image = image;
      e.stopPropagation();
    }

    function onMetadataChange(e, metadata) {
      model.metadata = metadata;
      e.stopPropagation();
    }

    function allowed() {
      return policy.ifAllowed({ rules: [['image', 'add_image']] });
    }

    function perform() {
      scope.image = {};

      return wizardModalService.modal({
        scope: scope,
        workflow: createWorkflow,
        submit: submit
      }).result.then(onSuccess);
    }

    function onSuccess() {
      return {
        created: [ {type: resourceType, id: 0}], // TODO: use id?
        updated: [],
        deleted: [],
        failed: []
      };
    }

    function submit() {
      return glance.createImage(model.image).then(onCreateImage);
    }

    function onCreateImage(response) {
      var newImage = response.data;
      toast.add('success', interpolate(message.success, [newImage.name]));
      saveMetadata(newImage).then(onUpdateMetadataSuccess, onUpdateMetadataFail);

      function onUpdateMetadataSuccess() {
        toast.add('success', interpolate(message.successMetadata, [newImage.name]));
        scope.$emit(events.CREATE_SUCCESS, newImage);
      }

      function onUpdateMetadataFail() {
        scope.$emit(events.CREATE_SUCCESS, newImage);
      }
    }

    function saveMetadata(image) {
      return metadataService.editMetadata('image', image.id, model.metadata, []);
    }

  } // end of createService
})(); // end of IIFE
