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
    .module('horizon.app.core.flavors')
    .factory('horizon.app.core.flavors.actions.update-metadata.service', updateMetadataService);

  updateMetadataService.$inject = [
    'horizon.app.core.metadata.modal.service',
    'horizon.framework.util.actions.action-result.service',
    'horizon.framework.util.q.extensions',
    'horizon.app.core.flavors.resourceType'
  ];

  /**
   * @ngDoc factory
   * @name horizon.app.core.flavors.actions.updateMetadataService
   *
   * @param {Object} metadataModalService
   * @param {Object} actionResultService
   * @param {Object} $qExtensions
   * @param {Object} flavorResourceType
   * @Description
   * Brings up the Update Metadata for flavor modal.
   * On submit, update the metadata of selected flavor.
   * On cancel, do nothing.
   *
   * @returns {Object} The service
   */
  function updateMetadataService(
    metadataModalService,
    actionResultService,
    $qExtensions,
    flavorResourceType
  ) {

    var service = {
      perform: perform,
      allowed: allowed
    };

    return service;

    //////////////

    function perform(flavor) {
      return metadataModalService.open('flavor', flavor.id)
        .result
        .then(onSuccess);

      function onSuccess() {
        return actionResultService.getActionResult()
          .updated(flavorResourceType, flavor.id)
          .result;
      }
    }

    function allowed() {
      return $qExtensions.booleanAsPromise(true);
    }

  } // end of updateMetadataService
})(); // end of IIFE
