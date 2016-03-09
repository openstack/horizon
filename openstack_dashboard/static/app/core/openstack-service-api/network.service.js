/**
 * Copyright 2016 IBM Corp.
 *
 * Licensed under the Apache License, Version 2.0 (the "License"); you may
 * not use this file except in compliance with the License. You may obtain
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
(function () {
  'use strict';

  angular
    .module('horizon.app.core.openstack-service-api')
    .factory('horizon.app.core.openstack-service-api.network', networkAPI);

  networkAPI.$inject = [
    'horizon.framework.util.http.service',
    'horizon.framework.widgets.toast.service'
  ];

  /**
   * @ngdoc service
   * @name networkAPI
   * @param {Object} apiService
   * @param {Object} toastService
   * @description Provides access to APIs that are common to nova network
   * and neutron.
   * @returns {Object} The service
   */
  function networkAPI(apiService, toastService) {
    var service = {
      getFloatingIps: getFloatingIps,
      getFloatingIpPools: getFloatingIpPools,
      allocateFloatingIp: allocateFloatingIp,
      associateFloatingIp: associateFloatingIp,
      disassociateFloatingIp: disassociateFloatingIp
    };

    return service;

    /////////////

    // Floating IPs

    /**
     * @name getFloatingIps
     * @description
     * Get a list of floating IP addresses.
     *
     * @returns {Object} An object with property "items". Each item is
     * a floating IP address.
     */
    function getFloatingIps() {
      return apiService.get('/api/network/floatingips/')
        .error(function () {
          toastService.add('error', gettext('Unable to retrieve floating IPs.'));
        });
    }

    /**
     * @name getFloatingIpPools
     * @description
     * Get a list of floating IP pools.
     *
     * @returns {Object} An object with property "items". Each item is
     * a floating IP address.
     */
    function getFloatingIpPools() {
      return apiService.get('/api/network/floatingippools/')
        .error(function () {
          toastService.add('error', gettext('Unable to retrieve floating IP pools.'));
        });
    }

    /**
     * @name allocateFloatingIp
     * @description
     * Allocate a floating IP address within a pool.
     *
     * @param {string} poolId
     * The Id of the pool in which to allocate the new floating IP address.
     *
     * @returns {Object} the new floating IP address on success.
     */
    function allocateFloatingIp(poolId) {
      return apiService.post('/api/network/floatingip/', { pool_id: poolId })
        .error(function () {
          toastService.add('error', gettext('Unable to allocate new floating IP address.'));
        });
    }

    /**
     * @name associateFloatingIp
     * @description
     * Associate a floating IP address with a port.
     *
     * @param {string} addressId
     * The Id of the floating IP address to associate.
     *
     * @param {string} portId
     * The Id of the port to associate.
     * @returns {Object} The result of the API call
     */
    function associateFloatingIp(addressId, portId) {
      var params = { address_id: addressId, port_id: portId };
      return apiService.patch('/api/network/floatingip/', params)
        .error(function () {
          toastService.add('error', gettext('Unable to associate floating IP address.'));
        });
    }

    /**
     * @name disassociateFloatingIp
     * @description
     * Disassociate a floating IP address.
     *
     * @param {string} addressId
     * The Id of the floating IP address to disassociate.
     * @returns {Object} The result of the API call
     */
    function disassociateFloatingIp(addressId) {
      return apiService.patch('/api/network/floatingip/', { address_id: addressId })
        .error(function () {
          toastService.add('error', gettext('Unable to disassociate floating IP address.'));
        });
    }

  }

}());
