/*
Copyright 2015 IBM Corp.

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
   * @name hz.api.cinderAPI
   * @description Provides direct access to Cinder APIs.
   */
  function CinderAPI(apiService) {

    // Volumes

    /**
     * @name hz.api.cinderAPI.getVolumes
     * @description
     * Get a list of volumes.
     *
     * The listing result is an object with property "items." Each item is
     * a volume.
     *
     * @param {Object} params
     * Query parameters. Optional.
     *
     * @param {string} param.search_opts
     * Filters to pass through the API.
     * For example, "status": "available" will show all available volumes.
     */
    this.getVolumes = function(params) {
      var config = (params) ? {'params': params} : {};
      return apiService.get('/api/cinder/volumes/', config)
        .error(function () {
          horizon.alert('error', gettext('Unable to retrieve volumes.'));
        });
    };

    // Volume Snapshots

    /**
     * @name hz.api.cinderAPI.getVolumeSnapshots
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
     */
    this.getVolumeSnapshots = function(params) {
      var config = (params) ? {'params': params} : {};
      return apiService.get('/api/cinder/volumesnapshots/', config)
        .error(function () {
          horizon.alert('error',
                        gettext('Unable to retrieve volume snapshots.'));
        });
    };
  }

  // Register it with the API module so that anybody using the
  // API module will have access to the Cinder APIs.
  angular.module('hz.api')
    .service('cinderAPI', ['apiService', CinderAPI]);
}());
