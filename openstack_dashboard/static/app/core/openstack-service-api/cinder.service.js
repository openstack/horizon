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
   * @name horizon.app.core.openstack-service-api.cinder
   * @description Provides direct access to Cinder APIs.
   */
  function cinderAPI(apiService, toastService) {
    var service = {
      getVolumes: getVolumes,
      getVolumeSnapshots: getVolumeSnapshots,
      getExtensions: getExtensions
    };

    return service;

    ///////////////

    // Volumes

    /**
     * @name horizon.app.core.openstack-service-api.cinder.getVolumes
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
    function getVolumes(params) {
      var config = (params) ? {'params': params} : {};
      return apiService.get('/api/cinder/volumes/', config)
        .error(function () {
          toastService.add('error', gettext('Unable to retrieve the volumes.'));
        });
    }

    // Volume Snapshots

    /**
     * @name horizon.app.core.openstack-service-api.cinder.getVolumeSnapshots
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
    function getVolumeSnapshots(params) {
      var config = (params) ? {'params': params} : {};
      return apiService.get('/api/cinder/volumesnapshots/', config)
        .error(function () {
          toastService.add('error',
                        gettext('Unable to retrieve the volume snapshots.'));
        });
    }

    // Cinder Extensions

    /**
     * @name horizon.app.core.openstack-service-api.cinder.getExtensions
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
     */
    function getExtensions(config) {
      return apiService.get('/api/cinder/extensions/', config)
        .error(function () {
          toastService.add('error', gettext('Unable to retrieve the extensions.'));
        });
    }

  }
}());
