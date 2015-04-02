/*
Copyright 2015, Hewlett-Packard Development Company, L.P.

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
*/
(function () {
  'use strict';

  /**
   * @ngdoc service
   * @name hz.api.glanceAPI
   * @description Provides direct pass through to Glance with NO abstraction.
   */
  function GlanceAPI(apiService) {

    // Images

     /**
     * @name hz.api.glanceAPI.getImage
     * @description
     * Get a single image by ID
     * @param {string} id
     * Specifies the id of the image to request.
     */
    this.getImage = function(id) {
      return apiService.get('/api/glance/images/' + id)
        .error(function () {
          horizon.alert('error', gettext('Unable to retrieve image.'));
      });
    };


    /**
     * @name hz.api.glanceAPI.getImages
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
    this.getImages = function(params) {
      var config = (params) ? { 'params' : params} : {};
      return apiService.get('/api/glance/images/', config)
        .error(function () {
          horizon.alert('error', gettext('Unable to retrieve images.'));
      });
    };

    // Metadata Definitions - Namespaces

    /**
     * @name hz.api.glanceAPI.getNamespaces
     * @description
     * Get a list of metadata definition namespaces.
     *
     * http://docs.openstack.org/developer/glance/metadefs-concepts.html
     *
     * The listing result is an object with property "items". Each item is
     * an namespace.
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
    this.getNamespaces = function(params, suppressError) {
      var config = (params) ? {'params' : params} : {};
      config.cache = true;

      var promise = apiService.get('/api/glance/metadefs/namespaces/', config);

      return suppressError ? promise : promise.error(function() {
          horizon.alert('error', gettext('Unable to retrieve namespaces.'));
        });
    };

  }

  // Register it with the API module so that anybody using the
  // API module will have access to the Glance APIs.

  angular.module('hz.api')
    .service('glanceAPI', ['apiService', GlanceAPI]);

}());
