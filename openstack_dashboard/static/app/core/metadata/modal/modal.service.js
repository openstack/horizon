/*
 * Copyright 2015, Intel Corp.
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
    .factory('horizon.app.core.metadata.modal.service', modalService);

  modalService.$inject = [
    '$uibModal',
    'horizon.app.core.basePath',
    'horizon.app.core.metadata.service',
    'horizon.app.core.metadata.modal.constants'
  ];

  /**
   * @ngdoc service
   * @name modalService
   */
  function modalService($uibModal, path, metadataService, modalConstants) {
    var service = {
      open: open
    };

    return service;

    /**
     * Open modal allowing to edit metadata
     *
     * @param {string} resource Metadata resource type
     * @param {string} id Object identifier to retrieve metadata from
     * @param {string} propertiesTarget The properties target, if the resource type has more than
     * one type of property.
     */
    function open(resource, id, propertiesTarget) {
      function resolveAvailable() {
        return metadataService.getNamespaces(resource, propertiesTarget);
      }
      function resolveExisting() {
        return metadataService.getMetadata(resource, id);
      }
      function resolveParams() {
        return {resource: resource, id: id};
      }

      var resolve = {
        available: resolveAvailable,
        existing: resolveExisting,
        params: resolveParams
      };
      var modalParams = {
        resolve: resolve,
        templateUrl: path + 'metadata/modal/modal.html'
      };
      return $uibModal.open(angular.extend(modalParams, modalConstants));
    }

  }
})();
