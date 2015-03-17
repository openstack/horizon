/**
 * Copyright 2015 IBM Corp.
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

    /**
   * @ngdoc service
   * @name hz.api.NeutronAPI
   * @description Provides access to Neutron APIs.
   */
  function NeutronAPI(apiService) {

     // Networks

     /**
      * @name hz.api.neturonAPI.getNetworks
      * @description
      * Get a list of networks for a tenant.
      *
      * The listing result is an object with property "items". Each item is
      * a network.
      */
    this.getNetworks = function() {
      return apiService.get('/api/neutron/networks/')
        .error(function () {
          horizon.alert('error', gettext('Unable to retrieve networks.'));
        });
    };

     /**
      * @name hz.api.neutronAPI.createNetwork
      * @description
      * Create a new network.
      * @returns The new network object on success.
      *
      * @param {Object} newNetwork
      * The network to create.  Required.
      *
      * Example new network object
      * {
      *    "name": "myNewNetwork",
      *    "admin_state_up": true,
      *    "net_profile_id" : "asdsarafssdaser",
      *    "shared": true,
      *    "tenant_id": "4fd44f30292945e481c7b8a0c8908869
      * }
      *
      * Description of properties on the network object
      *
      * @property {string} newNetwork.name
      * The name of the new network. Optional.
      *
      * @property {boolean} newNetwork.admin_state_up
      * The administrative state of the network, which is up (true) or
      * down (false). Optional.
      *
      * @property {string} newNetwork.net_profile_id
      * The network profile id. Optional.
      *
      * @property {boolean} newNetwork.shared
      * Indicates whether this network is shared across all tenants.
      * By default, only adminstative users can change this value. Optional.
      *
      * @property {string} newNetwork.tenant_id
      * The UUID of the tenant that will own the network.  This tenant can
      * be different from the tenant that makes the create network request.
      * However, only administative users can specify a tenant ID other than
      * their own.  You cannot change this value through authorization
      * policies.  Optional.
      *
      */
    this.createNetwork = function(newNetwork) {
      return apiService.post('/api/neutron/networks/', newNetwork)
        .error(function () {
          horizon.alert('error', gettext('Unable to create the network.'));
        });
    };

    // Subnets

     /**
      * @name hz.api.neutronAPI.getSubnets
      * @description
      * Get a list of subnets for a network.
      *
      * The listing result is an object with property "items". Each item is
      * a subnet.
      *
      * @param {string} network_id
      * The network id to retrieve subnets for. Required.
      */
    this.getSubnets = function(network_id) {
      return apiService.get('/api/neutron/subnets/', network_id)
        .error(function () {
          horizon.alert('error', gettext('Unable to retrieve subnets.'));
        });
    };

     /**
      * @name hz.api.neutronAPI.createSubnet
      * @description
      * Create a Subnet for given Network.
      * @returns The JSON representation of Subnet on success.
      *
      * @param {Object} newSubnet
      * The subnet to create.
      *
      * Example new subnet object
      * {
      *    "network_id": "d32019d3-bc6e-4319-9c1d-6722fc136a22",
      *    "ip_version": 4,
      *    "cidr": "192.168.199.0/24",
      *    "name": "mySubnet",
      *    "tenant_id": "4fd44f30292945e481c7b8a0c8908869,
      *    "allocation_pools": [
      *       {
      *          "start": "192.168.199.2",
      *          "end": "192.168.199.254"
      *       }
      *    ],
      *    "gateway_ip": "192.168.199.1",
      *    "id": "abce",
      *    "enable_dhcp": true,
      * }
      *
      * Description of properties on the subnet object
      * @property {string} newSubnet.network_id
      * The id of the attached network. Required.
      *
      * @property {number} newSubnet.ip_version
      * The IP version, which is 4 or 6. Required.
      *
      * @property {string} newSubnet.cidr
      * The CIDR. Required.
      *
      * @property {string} newSubnet.name
      * The name of the new subnet. Optional.
      *
      * @property {string} newSubnet.tenant_id
      * The ID of the tenant who owns the network.  Only administrative users
      * can specify a tenant ID other than their own. Optional.
      *
      * @property {string|Array} newSubnet.allocation_pools
      * The start and end addresses for the allocation pools.  Optional.
      *
      * @property {string} newSubnet.gateway_ip
      * The gateway IP address.  Optional.
      *
      * @property {string} newSubnet.id
      * The ID of the subnet. Optional.
      *
      * @property {boolean} newSubnet.enable_dhcp
      * Set to true if DHCP is enabled and false if DHCP is disabled. Optional.
      *
      */
    this.createSubnet = function(newSubnet) {
      return apiService.post('/api/neutron/subnets/', newSubnet)
        .error(function () {
          horizon.alert('error', gettext('Unable to create the subnet.'));
        });
    };

    // Ports

     /**
      * @name hz.api.neutronAPI.getPorts
      * @description
      * Get a list of ports for a network.
      *
      * The listing result is an object with property "items". Each item is
      * a port.
      *
      * @param {string} network_id
      * The network id to retrieve ports for. Required.
      */
    this.getPorts = function(network_id) {
      return apiService.get('/api/neutron/ports/', network_id)
        .error(function () {
          horizon.alert('error', gettext('Unable to retrieve ports.'));
        });
    };

  }

  angular.module('hz.api')
    .service('neutronAPI', ['apiService', NeutronAPI]);
}());
