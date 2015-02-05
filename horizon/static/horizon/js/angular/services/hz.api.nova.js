/*
Copyright 2014, Rackspace, US, Inc.

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
/*global angular,horizon*/
(function () {
  'use strict';

    /**
   * @ngdoc service
   * @name hz.api.novaAPI
   * @description Provides access to Nova APIs.
   */
  function NovaAPI(apiService) {

     // Keypairs

     /**
      * @name hz.api.novaAPI.getKeypairs
      * @description
      * Get a list of keypairs.
      *
      * The listing result is an object with property "items". Each item is
      * a keypair.
      */
    this.getKeypairs = function() {
      return apiService.get('/api/nova/keypairs/')
        .error(function () {
          horizon.alert('error', gettext('Unable to retrieve keypairs.'));
        });
    };

     /**
      * @name hz.api.novaAPI.createKeypair
      * @description
      * Create a new keypair.  This returns the new keypair object on success.
      *
      * @param {Object} newKeypair
      * The keypair to create.
      *
      * @param {string} newKeypair.name
      * The name of the new keypair. Required.
      *
      * @param {string} newKeypair.public_key
      * The public key.  Optional.
      */
    this.createKeypair = function(newKeypair) {
      return apiService.post('/api/nova/keypairs/', newKeypair)
        .error(function () {
          horizon.alert('error', gettext('Unable to create the keypair.'));
        });
    };

    // Availability Zones

     /**
      * @name hz.api.novaAPI.getAvailabilityZones
      * @description
      * Get a list of Availability Zones.
      *
      * The listing result is an object with property "items". Each item is
      * an availability zone.
      */
    this.getAvailabilityZones = function() {
      return apiService.get('/api/nova/availzones/')
        .error(function () {
          horizon.alert('error',
                        gettext('Unable to retrieve availability zones.'));
        });
    };

    // Limits

    /**
     * @name hz.api.novaAPI.getLimits
     * @description
     * Returns current limits.
     *
     * @example
     * The following is an example response:
     * {
     *   "maxImageMeta": 128,
     *   "maxPersonality": 5,
     *   "maxPersonalitySize": 10240,
     *   "maxSecurityGroupRules": 20,
     *   "maxSecurityGroups": 10,
     *   "maxServerGroupMembers": 10,
     *   "maxServerGroups": 10,
     *   "maxServerMeta": 128,
     *   "maxTotalCores": 20,
     *   "maxTotalFloatingIps": 10,
     *   "maxTotalInstances": 10,
     *   "maxTotalKeypairs": 100,
     *   "maxTotalRAMSize": 51200,
     *   "totalCoresUsed": 1,
     *   "totalFloatingIpsUsed": 0,
     *   "totalInstancesUsed": 1,
     *   "totalRAMUsed": 512,
     *   "totalSecurityGroupsUsed": 1,
     *   "totalServerGroupsUsed": 0
     * }
     */
    this.getLimits = function() {
      return apiService.get('/api/nova/limits/')
        .error(function () {
          horizon.alert('error', gettext('Unable to retrieve limits.'));
        });
    };

    // Servers

    /**
     * @name hz.api.novaAPI.createServer
     * @description
     * Create a server using the parameters supplied in the
     * newServer. The required parameters:
     *
     * "name", "source_id", "flavor_id", "key_name", "user_data"
     *     All strings
     * "security_groups"
     *     An array of one or more objects with a "name" attribute.
     *
     * Other parameters are accepted as per the underlying novaclient:
     * "block_device_mapping", "block_device_mapping_v2", "nics", "meta",
     * "availability_zone", "instance_count", "admin_pass", "disk_config",
     * "config_drive"
     *
     * This returns the new server object on success.
     */
    this.createServer = function(newServer) {
      return apiService.post('/api/nova/servers/', newServer)
        .error(function () {
          horizon.alert('error', gettext('Unable to create the server.'));
        });
    };
  }

  angular.module('hz.api')
    .service('novaAPI', ['apiService', NovaAPI]);
}());
