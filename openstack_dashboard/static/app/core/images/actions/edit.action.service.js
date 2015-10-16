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
    .factory('horizon.app.core.images.actions.edit.service', editService);

  editService.$inject = [
    '$q',
    'horizon.app.core.images.resourceType',
    'horizon.app.core.images.events',
    'horizon.app.core.images.actions.editWorkflow',
    'horizon.app.core.metadata.service',
    'horizon.app.core.openstack-service-api.glance',
    'horizon.app.core.openstack-service-api.policy',
    'horizon.app.core.openstack-service-api.userSession',
    'horizon.framework.util.actions.action-result.service',
    'horizon.framework.util.q.extensions',
    'horizon.framework.widgets.modal.wizard-modal.service',
    'horizon.framework.widgets.toast.service'
  ];

  /**
   * @ngDoc factory
   * @name horizon.app.core.images.actions.editService
   * @Description A service to open the user wizard.
   */
  function editService(
    $q,
    imageResourceType,
    events,
    editWorkflow,
    metadataService,
    glance,
    policy,
    userSessionService,
    actionResultService,
    $qExtensions,
    wizardModalService,
    toast
  ) {
    var message = {
      success: gettext('Image %s was successfully updated.'),
      successMetadata: gettext('Image metadata %s was successfully updated.')
    };
    var modifyImagePolicyCheck, scope, saveDeferred;

    var model = {
      image: {},
      metadata: {}
    };

    var service = {
      initScope: initScope,
      allowed: allowed,
      perform: perform
    };

    return service;

    //////////////

    function initScope($scope) {
      scope = $scope;
      modifyImagePolicyCheck = policy.ifAllowed({rules: [['image', 'modify_image']]});
    }

    function allowed(image) {
      return $q.all([
        modifyImagePolicyCheck,
        userSessionService.isCurrentProject(image.owner),
        isActive(image)
      ]);
    }

    function perform(image) {
      var deferred = glance.getImage(image.id);
      deferred.then(onLoad);
      scope.imagePromise = deferred;

      function onLoad(response) {
        var localImage = response.data;
        model.image = localImage;
      }

      wizardModalService.modal({
        scope: scope,
        workflow: editWorkflow,
        submit: submit
      }).result.catch(cancel);

      saveDeferred = $q.defer();
      return saveDeferred.promise;
    }

    function cancel() {
      saveDeferred.reject();
    }

    function submit() {
      return saveMetadata().then(onSaveMetadata, onFailMetadata);
    }

    function onFailMetadata() {
      glance.updateImage(model.image).then(onUpdateImageSuccess, onUpdateImageFail);
    }

    function onSaveMetadata() {
      toast.add('success', interpolate(message.successMetadata, [model.image.name]));
      glance.updateImage(model.image).then(onUpdateImageSuccess, onUpdateImageFail);
    }

    function onUpdateImageSuccess() {
      toast.add('success', interpolate(message.success, [model.image.name]));
      saveDeferred.resolve(actionResultService.getActionResult()
        .updated(imageResourceType, model.image.id)
        .result);
    }

    function onUpdateImageFail() {
      saveDeferred.reject(actionResultService.getActionResult()
        .failed(imageResourceType, model.image.id)
        .result);
    }

    function saveMetadata() {
      var imageId = model.image.id;
      var deferred = $q.defer();

      metadataService.getMetadata('image', imageId).then(onMetadataGet);

      function onMetadataGet(response) {
        var removed = angular.copy(response.data);
        angular.forEach(model.metadata, function(value, key) {
          delete removed[key];
        });

        deferred.resolve(
          metadataService.editMetadata('image', imageId, model.metadata, Object.keys(removed))
        );
      }

      return deferred.promise;
    }

    function isActive(image) {
      return $qExtensions.booleanAsPromise(image.status === 'active');
    }

  } // end of editService
})(); // end of IIFE
