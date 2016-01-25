/*
 * Copyright 2015, Intel Corp.
 *    (c) Copyright 2015 Hewlett-Packard Development Company, L.P.
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *    http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */
(function () {
  'use strict';

  angular
    .module('horizon.app.core.metadata.modal')
    .controller('MetadataModalHelperController', MetadataModalHelperController);

  MetadataModalHelperController.$inject = [
    '$window',
    'horizon.app.core.metadata.modal.service'
  ];

  /**
   * @ngdoc controller
   * @name horizon.app.core.metadata.modal.controller:MetadataModalHelperController
   * @description
   * Helper controller used by Horizon part written in Django.
   */
  function MetadataModalHelperController($window, metadataModalService) {
    //NOTE(bluex): controller should be removed when reload is no longer needed
    var ctrl = this;

    ctrl.openMetadataModal = openMetadataModal;

    /**
     * Open modal allowing to edit metadata
     *
     * @param {string} resource Metadata resource type
     * @param {string} id Object identifier to retrieve metadata from
     * @param {boolean=} requireReload Whether to reload page when metadata successfully updated
     * @param {string} propertiesTarget The properties target, if the resource type has more than
     * one type of property.
     */
    function openMetadataModal(resource, id, requireReload, propertiesTarget) {
      metadataModalService.open(resource, id, propertiesTarget)
        .result
        .then(onOpened);

      function onOpened() {
        if (requireReload) {
          $window.location.reload();
        }
      }
    }
  }
})();
