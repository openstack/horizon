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
    .factory('horizon.app.core.images.actions.launch-instance.service', launchInstanceService);

  launchInstanceService.$inject = [
    '$q',
    'horizon.app.core.images.non_bootable_image_types',
    'horizon.dashboard.project.workflow.launch-instance.modal.service',
    'horizon.framework.util.q.extensions'
  ];

  /**
   * @ngDoc factory
   * @name horizon.app.core.images.actions.launchInstanceService
   *
   * @Description
   * Brings up the Launch Instance for image modal.
   * On submit, launch the instance for the Image.
   * On cancel, do nothing.
   */
  function launchInstanceService(
    $q,
    nonBootableImageTypes,
    launchInstanceModal,
    $qExtensions
  ) {
    var service = {
      perform: perform,
      allowed: allowed
    };

    return service;

    //////////////

    function perform(image) {
      return launchInstanceModal.open({
        successUrl: '/project/instances',
        'imageId': image.id
      });
    }

    function allowed(image) {
      return $q.all([isBootable(image), isActive(image)]);
    }

    function isActive(image) {
      return $qExtensions.booleanAsPromise(image.status === 'active');
    }

    function isBootable(image) {
      return $qExtensions.booleanAsPromise(
        nonBootableImageTypes.indexOf(image.container_format) < 0
      );
    }

  } // end of launchInstanceService
})(); // end of IIFE
