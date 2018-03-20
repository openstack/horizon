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
      getVolumeMetadata: getVolumeMetadata,
      getVolumeSnapshotMetadata: getVolumeSnapshotMetadata,
      getVolumeTypeMetadata: getVolumeTypeMetadata,
      getVolumeType: getVolumeType,
      getDefaultVolumeType: getDefaultVolumeType,
      getVolumeSnapshots: getVolumeSnapshots,
      getExtensions: getExtensions,
      getQoSSpecs: getQoSSpecs,
      getAvailabilityZones:getAvailabilityZones,
      createVolume: createVolume,
      getAbsoluteLimits: getAbsoluteLimits,
      getServices: getServices,
      getDefaultQuotaSets: getDefaultQuotaSets,
      setDefaultQuotaSets: setDefaultQuotaSets,
      updateProjectQuota: updateProjectQuota,
      editVolumeMetadata: editVolumeMetadata,
      editVolumeSnapshotMetadata: editVolumeSnapshotMetadata,
      editVolumeTypeMetadata:editVolumeTypeMetadata
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

    function getVolumeMetadata(id) {
      return apiService.get('/api/cinder/volumes/' + id + '/metadata')
        .error(function () {
          toastService.add('error', gettext('Unable to retrieve the volume metadata.'));
        });
    }

    function getVolumeSnapshotMetadata(id) {
      return apiService.get('/api/cinder/volumesnapshots/' + id + '/metadata')
        .error(function () {
          toastService.add('error', gettext('Unable to retrieve the snapshot metadata.'));
        });
    }

    function getVolumeTypeMetadata(id) {
      return apiService.get('/api/cinder/volumetypes/' + id + '/metadata')
        .error(function () {
          toastService.add('error', gettext('Unable to retrieve the volume type metadata.'));
        });
    }

    function editVolumeMetadata(id, updated, removed) {
      return apiService.patch(
        '/api/cinder/volumes/' + id + '/metadata',
        {
          updated: updated,
          removed: removed
        }
      ).error(function () {
        toastService.add('error', gettext('Unable to edit volume metadata.'));
      });
    }

    function editVolumeSnapshotMetadata(id, updated, removed) {
      return apiService.patch(
        '/api/cinder/volumesnapshots/' + id + '/metadata',
        {
          updated: updated,
          removed: removed
        }
      ).error(function () {
        toastService.add('error', gettext('Unable to edit snapshot metadata.'));
      });
    }

    function editVolumeTypeMetadata(id, updated, removed) {
      return apiService.patch(
        '/api/cinder/volumetypes/' + id + '/metadata',
        {
          updated: updated,
          removed: removed
        }
      ).error(function () {
        toastService.add('error', gettext('Unable to edit volume type metadata.'));
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
          toastService.add('error', gettext('Unable to retrieve the volume snapshots.'));
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
     *        "alias": "OS-SCH-HNT",
     *        "description": "Pass arbitrary key/value pairs to the scheduler.",
     *        "links": [],
     *        "name": "SchedulerHints",
     *        "updated": "2013-04-18T00:00:00+00:00"
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

    // Default Quota Sets

    /**
     * @name horizon.app.core.openstack-service-api.cinder.getDefaultQuotaSets
     * @description
     * Get default quotasets
     *
     * The listing result is an object with property "items." Each item is
     * a quota.
     *
     */
    function getDefaultQuotaSets() {
      return apiService.get('/api/cinder/quota-sets/defaults/')
        .error(function () {
          toastService.add('error', gettext('Unable to retrieve the default quotas.'));
        });
    }

    /**
     * @name horizon.app.core.openstack-service-api.cinder.setDefaultQuotaSets
     * @description
     * Set default quota sets
     *
     */
    function setDefaultQuotaSets(quotas) {
      return apiService.patch('/api/cinder/quota-sets/defaults/', quotas)
        .error(function () {
          toastService.add('error', gettext('Unable to set the default quotas.'));
        });
    }

    // Quota Sets

    /**
     * @name updateProjectQuota
     * @description
     * Update a single project quota data.
     * @param {application/json} quota
     * A JSON object with the attributes to set to new quota values.
     * @param {string} projectId
     * Specifies the id of the project that'll have the quota data updated.
     */
    function updateProjectQuota(quota, projectId) {
      var url = '/api/cinder/quota-sets/' + projectId;
      return apiService.patch(url, quota)
        .error(function() {
          toastService.add('error', gettext('Unable to update project quota data.'));
        });
    }

    // Availability Zones

    /**
     * @name getAvailabilityZones
     * @description
     * Get a list of Availability Zones.
     *
     * The listing result is an object with property "items". Each item is
     * an availability zone.
     * @returns {Object} The result of the API call
     */
    function getAvailabilityZones() {
      return apiService.get('/api/cinder/availzones/')
        .error(function () {
          toastService.add('error',
                        gettext('Unable to retrieve the volume availability zones.'));
        });
    }
  }

}());
