/**
 * Copyright 2015 IBM Corp.
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
    .factory('horizon.app.core.openstack-service-api.cinder', cinderAPI);

  cinderAPI.$inject = [
    'horizon.framework.util.http.service',
    'horizon.framework.widgets.toast.service'
  ];

  /**
   * @ngdoc service
   * @param {Object} apiService
   * @param {Object} toastService
   * @name cinder
   * @description Provides direct access to Cinder APIs.
   * @returns {Object} The service
   */
  function cinderAPI(apiService, toastService) {
    var service = {
      getVolumes: getVolumes,
      getVolume: getVolume,
      getVolumeTypes: getVolumeTypes,
      getVolumeType: getVolumeType,
      getDefaultVolumeType: getDefaultVolumeType,
      getVolumeSnapshots: getVolumeSnapshots,
      getExtensions: getExtensions,
      getQoSSpecs: getQoSSpecs,
      createVolume: createVolume,
      getAbsoluteLimits: getAbsoluteLimits,
      getServices: getServices
    };

    return service;

    ///////////////

    // Volumes

    /**
     * @name getVolumes
     * @description
     * Get a list of volumes.
     *
     * The listing result is an object with property "items." Each item is
     * a volume.
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
     * @param {string} param.search_opts
     * Filters to pass through the API.
     * For example, "status": "available" will show all available volumes.
     * @returns {Object} The result of the API call
     */
    function getVolumes(params) {
      var config = params ? {'params': params} : {};
      return apiService.get('/api/cinder/volumes/', config)
        .error(function () {
          toastService.add('error', gettext('Unable to retrieve the volumes.'));
        });
    }

    /**
     * @name getVolume
     * @description
     * Get a single Volume by ID.
     *
     * @param {string} id
     * Specifies the id of the Volume to request.
     *
     * @returns {Object} The result of the API call
     */
    function getVolume(id) {
      return apiService.get('/api/cinder/volumes/' + id)
        .error(function () {
          toastService.add('error', gettext('Unable to retrieve the volume.'));
        });
    }

    /**
     * @name createVolume
     * @param {Object} newVolume - The new volume object
     * @description
     * Create a volume.
     * @returns {Object} The result of the API call
     */
    function createVolume(newVolume) {
      return apiService.post('/api/cinder/volumes/', newVolume)
        .error(function () {
          toastService.add('error', gettext('Unable to create the volume.'));
        });
    }

    // Volume Types

    /**
     * @name getVolumeTypes
     * @description
     * Get a list of volume types.
     *
     * The listing result is an object with property "items." Each item is
     * a volume type.
     *
     * @returns {Object} The result of the API call
     */
    function getVolumeTypes() {
      return apiService.get('/api/cinder/volumetypes/')
        .error(function () {
          toastService.add('error', gettext('Unable to retrieve the volume types.'));
        });
    }

    /**
     * @name getVolumeType
     * @description
     * Get a single Volume Type by ID.
     *
     * @param {string} id
     * Specifies the id of the Volume Type to request.
     *
     * @returns {Object} The result of the API call
     */
    function getVolumeType(id) {
      return apiService.get('/api/cinder/volumetypes/' + id)
        .error(function () {
          toastService.add('error', gettext('Unable to retrieve the volume type.'));
        });
    }

    /**
     * @name getDefaultVolumeType
     * @description
     * Get the default Volume Type
     *
     * @returns {Object} The result of the API call
     */
    function getDefaultVolumeType() {
      return apiService.get('/api/cinder/volumetypes/default')
        .error(function () {
          toastService.add('error', gettext('Unable to retrieve the default volume type.'));
        });
    }

    // Volume Snapshots

    /**
     * @name getVolumeSnapshots
     * @description
     * Get a list of volume snapshots.
     *
     * The listing result is an object with property "items." Each item is
     * a volume snapshot.
     *
     * @param {Object} params
     * Query parameters. Optional.
     *
     * @param {string} param.search_opts
     * Filters to pass through the API.
     * For example, "status": "available" will show all available volume
     * snapshots.
     * @returns {Object} The result of the API call
     */
    function getVolumeSnapshots(params) {
      var config = params ? {'params': params} : {};
      return apiService.get('/api/cinder/volumesnapshots/', config)
        .error(function () {
          toastService.add('error',
                        gettext('Unable to retrieve the volume snapshots.'));
        });
    }

    // Cinder Extensions

    /**
     * @name getExtensions
     * @param {Object} config - The configuration for retrieving the extensions
     * @description
     * Returns a list of enabled extensions.
     *
     * The listing result is an object with property "items". Each item is
     * an extension.
     * @example
     * The following is an example response:
     *
     *  {
     *    "items": [
     *      {
     *        "alias": "NMN",
     *        "description": "Multiple network support.",
     *        "links": [],
     *        "name": "Multinic",
     *        "namespace": "http://docs.openstack.org/compute/ext/multinic/api/v1.1",
     *        "updated": "2011-06-09T00:00:00Z"
     *      }
     *    ]
     *  }
     * @returns {Object} The result of the API call
     */
    function getExtensions(config) {
      return apiService.get('/api/cinder/extensions/', config)
        .error(function () {
          toastService.add('error', gettext('Unable to retrieve the extensions.'));
        });
    }

    // Cinder Services

    /**
    * @name getServices
    * @description Get the list of Cinder services.
    *
    * @returns {Object} An object with property "services." Each item is
    * a service.
    */
    function getServices() {
      return apiService.get('/api/cinder/services/')
        .error(function () {
          toastService.add('error', gettext('Unable to retrieve the cinder services.'));
        });
    }

    /**
     * @name getQoSSpecs
     * @description
     * Get a list of Quality of Service.
     *
     * The listing result is an object with property "items." Each item is
     * a Quality of Service Spec.
     *
     * @param {Object} params
     * Query parameters. Optional.
     * @returns {Object} The result of the API call
     *
     */
    function getQoSSpecs(params) {
      var config = params ? {'params': params} : {};
      return apiService.get('/api/cinder/qosspecs/', config)
        .error(function () {
          toastService.add('error',
            gettext('Unable to retrieve the QoS Specs.'));
        });
    }

    /**
     * @name getAbsoluteLimits
     * @description
     * Get the limits for the current tenant.
     *
     * @returns {Object} The result of the API call
     */
    function getAbsoluteLimits() {
      return apiService.get('/api/cinder/tenantabsolutelimits/')
        .error(function () {
          toastService.add('error',
            gettext('Unable to retrieve the Absolute Limits.'));
        });
    }
  }
}());
