/**
 * Copyright 2015, Hewlett-Packard Development Company, L.P.
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
    .module('horizon.app.core.openstack-service-api')
    .factory('horizon.app.core.openstack-service-api.glance', glanceAPI);

  glanceAPI.$inject = [
    'horizon.framework.util.http.service',
    'horizon.framework.widgets.toast.service'
  ];

  /**
   * @ngdoc service
   * @name horizon.app.core.openstack-service-api.glance
   * @description Provides direct pass through to Glance with NO abstraction.
   */
  function glanceAPI(apiService, toastService) {
    var service = {
      getVersion: getVersion,
      getImage: getImage,
      createImage: createImage,
      updateImage: updateImage,
      deleteImage: deleteImage,
      getImageProps: getImageProps,
      editImageProps: editImageProps,
      getImages: getImages,
      getNamespaces: getNamespaces,
      getResourceTypes: getResourceTypes
    };

    return service;

    ///////////////

    // Version

    /**
     * @name horizon.app.core.openstack-service-api.glance.getVersion
     * @description
     * Get the version of the Glance API
     */
    function getVersion() {
      return apiService.get('/api/glance/version/')
        .error(function () {
          toastService.add('error', gettext('Unable to get the Glance service version.'));
        });
    }

    // Images

    /**
     * @name horizon.app.core.openstack-service-api.glance.getImage
     * @description
     * Get a single image by ID
     *
     * @param {string} id
     * Specifies the id of the image to request.
     *
     */
    function getImage(id) {
      return apiService.get('/api/glance/images/' + id + '/')
        .error(function () {
          toastService.add('error', gettext('Unable to retrieve the image.'));
        });
    }

    /**
     * @name horizon.app.core.openstack-service-api.glance.createImage
     * @description
     * Create a new image. This returns the new image object on success.
     *
     * @param {object} image
     * The image to create
     *
     * @param {string} image.name
     * Name of the image. Required.
     *
     * @param {string} image.description
     * Description of the image. Optional.
     *
     * @param {string} image.source_type
     * Source Type for the image. Only 'url' is supported. Required.
     *
     * @param {string} image.disk_format
     * Format of the image. Required.
     *
     * @param {string} image.kernel
     * Kernel to use for the image. Optional.
     *
     * @param {string} image.ramdisk
     * RamDisk to use for the image. Optional.
     *
     * @param {string} image.architecture
     * Architecture the image. Optional.
     *
     * @param {string} image.min_disk
     * The minimum disk size required to boot the image. Optional.
     *
     * @param {string} image.min_ram
     * The minimum memory size required to boot the image. Optional.
     *
     * @param {boolean} image.visibility
     * values of 'public', 'private', and 'shared' are valid. Required.
     *
     * @param {boolean} image.protected
     * True if the image is protected, false otherwise. Required.
     *
     * @param {boolean} image.import_data
     * True to import the image data to the image service otherwise
     * image data will be used in its current location
     *
     * Any parameters not listed above will be assigned as custom properites.
     *
     */
    function createImage(image) {
      return apiService.post('/api/glance/images/', image)
        .error(function () {
          toastService.add('error', gettext('Unable to create the image.'));
        });
    }

    /**
     * @name horizon.app.core.openstack-service-api.glance.getImage
     * @description
     * Update an existing image.
     *
     * @param {object} image
     * The image to update
     *
     * @param {string} image.id
     * ID of the image to update. Required. Read Only.
     *
     * @param {string} image.name
     * Name of the image. Required.
     *
     * @param {string} image.description
     * Description of the image. Optional.
     *
     * @param {string} image.disk_format
     * Disk format of the image. Required.
     *
     * @param {string} image.kernel
     * Kernel to use for the image. Optional.
     *
     * @param {string} image.ramdisk
     * RamDisk to use for the image. Optional.
     *
     * @param {string} image.architecture
     * Architecture the image. Optional.
     *
     * @param {string} image.min_disk
     * The minimum disk size required to boot the image. Optional.
     *
     * @param {string} image.min_ram
     * The minimum memory size required to boot the image. Optional.
     *
     * @param {boolean} image.visibility
     * Values of 'public', 'private', and 'shared' are valid. Required.
     *
     * @param {boolean} image.protected
     * True if the image is protected, false otherwise. Required.
     *
     * Any parameters not listed above will be assigned as custom properites.
     */
    function updateImage(image) {
      return apiService.patch('/api/glance/images/' + image.id + '/', image)
        .error(function () {
          toastService.add('error', gettext('Unable to update the image.'));
        });
    }

    /**
     * @name horizon.app.core.openstack-service-api.glance.deleteImage
     * @description
     * Deletes single Image by ID.
     *
     * @param {string} imageId
     * The Id of the image to delete.
     *
     * @param {boolean} suppressError
     * If passed in, this will not show the default error handling
     *
     */
    function deleteImage(imageId, suppressError) {
      var promise = apiService.delete('/api/glance/images/' + imageId + '/');

      return suppressError ? promise : promise.error(function() {
        var msg = gettext('Unable to delete the image with id: %(id)s');
        toastService.add('error', interpolate(msg, { id: imageId }, true));
      });
    }

    /**
     * @name horizon.app.core.openstack-service-api.glance.getImageProps
     * @description
     * Get an image custom properties by image ID
     * @param {string} id Specifies the id of the image to request.
     */
    function getImageProps(id) {
      return apiService.get('/api/glance/images/' + id + '/properties/')
        .error(function () {
          toastService.add('error', gettext('Unable to retrieve the image custom properties.'));
        });
    }

    /**
     * @name horizon.app.core.openstack-service-api.glance.editImageProps
     * @description
     * Update an image custom properties by image ID
     * @param {string} id Specifies the id of the image to request.
     * @param {object} updated New metadata definitions.
     * @param {[]} removed Names of removed metadata definitions.
     */
    function editImageProps(id, updated, removed) {
      return apiService.patch(
        '/api/glance/images/' + id + '/properties/',
        {
          updated: updated,
          removed: removed
        }
      )
      .error(function () {
        toastService.add('error', gettext('Unable to edit the image custom properties.'));
      });
    }

    /**
     * @name horizon.app.core.openstack-service-api.glance.getImages
     * @description
     * Get a list of images.
     *
     * The listing result is an object with property "items". Each item is
     * an image.
     *
     * @param {Object} params
     * Query parameters. Optional.
     *
     * @param {boolean} params.paginate
     * True to paginate automatically.
     *
     * @param {string} params.marker
     * Specifies the image of the last-seen image.
     *
     * The typical pattern of limit and marker is to make an
     * initial limited request and then to use the last
     * image from the response as the marker parameter
     * in a subsequent limited request. With paginate, limit
     * is automatically set.
     *
     * @param {string} params.sort_dir
     * The sort direction ('asc' or 'desc').
     *
     * @param {string} params.sort_key
     *   The field to sort on (for example, 'created_at').
     *   Default is created_at.
     *
     * @param {string} params.other
     * Any additional request parameters will be passed through the API as
     * filters. For example "name" : "fedora" would filter on the fedora name.
     */
    function getImages(params) {
      var config = params ? { 'params' : params} : {};
      return apiService.get('/api/glance/images/', config)
        .error(function () {
          toastService.add('error', gettext('Unable to retrieve the images.'));
        });
    }

    // Metadata Definitions - Namespaces

    /**
     * @name horizon.app.core.openstack-service-api.glance.getNamespaces
     * @description
     * Get a list of metadata definition namespaces.
     *
     * http://docs.openstack.org/developer/glance/metadefs-concepts.html
     *
     * The listing result is an object with property "items". Each item is
     * a namespace.
     *
     * @description
     * Get a list of namespaces.
     *
     * The listing result is an object with property "items". Each item is
     * a namespace.
     *
     * @param {Object} params
     * Query parameters. Optional.
     *
     * @param {string} params.resource_type
     * Namespace resource type.
     *
     * @param {string} params.properties_target
     * The properties target, if the resource type has more than one type
     * of property. For example, the OS::Nova::Server resource type has
     * "metadata" and "scheduler_hints" properties targets.
     *
     * @param {boolean} params.paginate
     * True to paginate automatically.
     *
     * @param {string} params.marker
     * Specifies the namespace of the last-seen namespace.
     *
     * The typical pattern of limit and marker is to make an
     * initial limited request and then to use the last
     * namespace from the response as the marker parameter
     * in a subsequent limited request. With paginate, limit
     * is automatically set.
     *
     * @param {string} params.sort_dir
     * The sort direction ('asc' or 'desc').
     *
     * @param {string} params.sort_key
     *   The field to sort on (for example, 'created_at').
     *   Default is namespace.
     *
     * @param {string} params.other
     * Any additional request parameters will be passed through the API as
     * filters.
     *
     * @param {boolean} suppressError
     * If passed in, this will not show the default error handling
     * (horizon alert). The glance API may not have metadata definitions
     * enabled.
     */
    function getNamespaces(params, suppressError) {
      var config = params ? {'params' : params} : {};
      config.cache = true;

      var promise = apiService.get('/api/glance/metadefs/namespaces/', config);

      return suppressError ? promise : promise.error(function() {
          toastService.add('error', gettext('Unable to retrieve the namespaces.'));
        });
    }

    /**
     * @name horizon.app.core.openstack-service-api.glance.getResourceTypes
     * @description
     * Get a list of metadata definition resource types.
     *
     * http://docs.openstack.org/developer/glance/metadefs-concepts.html
     *
     * The listing result is an object with property "items".
     * Each item is a resource type. Resource types are Strings that
     * correlate to Heat and Searchlight resource types.
     * For example: OS::Glance::Image and OS::Nova::Server.
     *
     */
    function getResourceTypes() {
      var config = {
        cache: true
      };

      return apiService
        .get('/api/glance/metadefs/resourcetypes/', config)
        .error(function() {
          toastService.add('error', gettext('Unable to retrieve the resource types.'));
        });
    }

  }
}());
