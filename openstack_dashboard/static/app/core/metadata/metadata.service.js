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
    .module('horizon.app.core.metadata')
    .factory('horizon.app.core.metadata.service', metadataService);

  metadataService.$inject = [
    'horizon.app.core.openstack-service-api.nova',
    'horizon.app.core.openstack-service-api.glance'
  ];

  /**
   * @ngdoc service
   * @name metadataService
   * @description
   *
   * Unified acquisition and modification of metadata.
   */
  function metadataService(nova, glance) {
    var service = {
      getMetadata: getMetadata,
      editMetadata: editMetadata,
      getNamespaces: getNamespaces
    };

    return service;

    /**
     * Get metadata from specified resource.
     *
     * @param {string} resource Resource type.
     * @param {string} id Resource identifier.
     */
    function getMetadata(resource, id) {
      return {
        aggregate: nova.getAggregateExtraSpecs,
        flavor: nova.getFlavorExtraSpecs,
        image: glance.getImageProps
      }[resource](id);
    }

    /**
     * Edit metadata of specified resource.
     *
     * @param {string} resource Resource type.
     * @param {string} id Resource identifier.
     * @param {object} updated New metadata.
     * @param {[]} removed Names of removed metadata.
     */
    function editMetadata(resource, id, updated, removed) {
      return {
        aggregate: nova.editAggregateExtraSpecs,
        flavor: nova.editFlavorExtraSpecs,
        image: glance.editImageProps
      }[resource](id, updated, removed);
    }

    /**
     * Get available metadata namespaces for specified resource.
     *
     * @param {string} resource Resource type.
     */
    function getNamespaces(resource) {
      return glance.getNamespaces({
        resource_type: {
          aggregate: 'OS::Nova::Aggregate',
          flavor: 'OS::Nova::Flavor',
          image: 'OS::Glance::Image'
        }[resource]
      }, false);
    }
  }
})();
