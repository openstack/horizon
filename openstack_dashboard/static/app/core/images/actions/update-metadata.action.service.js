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
    'horizon.app.core.images.events',
    'horizon.app.core.metadata.modal.service',
    'horizon.app.core.openstack-service-api.userSession',
    'horizon.framework.util.q.extensions'
  ];

  /**
   * @ngDoc factory
   * @name horizon.app.core.images.actions.updateMetadataService
   *
   * @Description
   * Brings up the Update Metadata for image modal.
   * On submit, update the metadata of selected image.
   * On cancel, do nothing.
   */
  function updateMetadataService(
    $q,
    events,
    metadataModalService,
    userSessionService,
    $qExtensions
  ) {
    var scope;

    var service = {
      initScope: initScope,
      perform: perform,
      allowed: allowed
    };

    return service;

    //////////////

    function initScope(newScope) {
      scope = newScope;
    }

    function perform(image) {
      return metadataModalService.open('image', image.id)
        .result
        .then(onSuccess);

      function onSuccess() {
        scope.$emit(events.UPDATE_METADATA_SUCCESS, [image.id]);
        return {
          // Object intentionally left blank. This data is passed to
          // code that holds this action's promise. In the future, it may
          // contain entity IDs and types that were modified by this action.
        };
      }
    }

    function allowed(image) {
      return $q.all([userSessionService.isCurrentProject(image.owner), isActive(image)]);
    }

    function isActive(image) {
      return $qExtensions.booleanAsPromise(image.status === 'active');
    }

  } // end of updateMetadataService
})(); // end of IIFE
