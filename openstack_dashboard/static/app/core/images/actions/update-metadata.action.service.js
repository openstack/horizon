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
    .factory('horizon.app.core.images.actions.update-metadata.service', updateMetadataService);

  updateMetadataService.$inject = [
    '$q',
    'horizon.app.core.metadata.modal.service',
    'horizon.app.core.openstack-service-api.policy',
    'horizon.framework.util.actions.action-result.service',
    'horizon.framework.util.q.extensions',
    'horizon.app.core.images.resourceType'
  ];

  /**
   * @ngDoc factory
   * @name horizon.app.core.images.actions.updateMetadataService
   *
   * @param {Object} $q
   * @param {Object} metadataModalService
   * @param {Object} policy
   * @param {Object} $qExtensions
   * @Description
   * Brings up the Update Metadata for image modal.
   * On submit, update the metadata of selected image.
   * On cancel, do nothing.
   *
   * @returns {Object} The service
   */
  function updateMetadataService(
    $q,
    metadataModalService,
    policy,
    actionResultService,
    $qExtensions,
    imageResourceType
  ) {

    var service = {
      perform: perform,
      allowed: allowed
    };

    return service;

    //////////////

    function perform(image) {
      return metadataModalService.open('image', image.id)
        .result
        .then(onSuccess);

      function onSuccess() {
        // To make the result of this action generically useful, reformat the return
        // from the deleteModal into a standard form
        return actionResultService.getActionResult()
          .updated(imageResourceType, image.id)
          .result;
      }
    }

    function allowed(image) {
      return $q.all([
        policy.ifAllowed({rules: [['image', 'modify_metadef_object']]}),
        isActive(image)
      ]);
    }

    function isActive(image) {
      return $qExtensions.booleanAsPromise(image.status === 'active');
    }

  } // end of updateMetadataService
})(); // end of IIFE
