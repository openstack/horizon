/**
 * Copyright 2014, Rackspace, US, Inc.
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
    .factory('horizon.app.core.openstack-service-api.nova', NovaAPI);

  NovaAPI.$inject = [
    'horizon.framework.util.http.service',
    'horizon.framework.widgets.toast.service'
  ];

  /**
   * @ngdoc service
   * @name horizon.app.core.openstack-service-api.nova
   * @description Provides access to Nova APIs.
   */
  function NovaAPI(apiService, toastService) {

    var service = {
      getKeypairs: getKeypairs,
      createKeypair: createKeypair,
      getAvailabilityZones: getAvailabilityZones,
      getLimits: getLimits,
      createServer: createServer,
      getServer: getServer,
      getExtensions: getExtensions,
      getFlavors: getFlavors,
      getFlavor: getFlavor,
      getFlavorExtraSpecs: getFlavorExtraSpecs,
      editFlavorExtraSpecs: editFlavorExtraSpecs,
      getAggregateExtraSpecs: getAggregateExtraSpecs,
      editAggregateExtraSpecs: editAggregateExtraSpecs
    };

    return service;

    ///////////

    // Keypairs

    /**
     * @name horizon.app.core.openstack-service-api.nova.getKeypairs
     * @description
     * Get a list of keypairs.
     *
     * The listing result is an object with property "items". Each item is
     * a keypair.
     */
    function getKeypairs() {
      return apiService.get('/api/nova/keypairs/')
        .error(function () {
          toastService.add('error', gettext('Unable to retrieve the keypairs.'));
        });
    }

    /**
     * @name horizon.app.core.openstack-service-api.nova.createKeypair
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
    function createKeypair(newKeypair) {
      return apiService.post('/api/nova/keypairs/', newKeypair)
        .error(function () {
          if (angular.isDefined(newKeypair.public_key)) {
            toastService.add('error', gettext('Unable to import the keypair.'));
          } else {
            toastService.add('error', gettext('Unable to create the keypair.'));
          }
        });
    }

    // Availability Zones

    /**
     * @name horizon.app.core.openstack-service-api.nova.getAvailabilityZones
     * @description
     * Get a list of Availability Zones.
     *
     * The listing result is an object with property "items". Each item is
     * an availability zone.
     */
    function getAvailabilityZones() {
      return apiService.get('/api/nova/availzones/')
        .error(function () {
          toastService.add('error',
                        gettext('Unable to retrieve the availability zones.'));
        });
    }

    // Limits

    /**
     * @name horizon.app.core.openstack-service-api.nova.getLimits
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
    function getLimits() {
      return apiService.get('/api/nova/limits/')
        .error(function () {
          toastService.add('error', gettext('Unable to retrieve the limits.'));
        });
    }

    // Servers

    /**
     * @name horizon.app.core.openstack-service-api.nova.createServer
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
    function createServer(newServer) {
      return apiService.post('/api/nova/servers/', newServer)
        .error(function () {
          toastService.add('error', gettext('Unable to create the server.'));
        });
    }

    /**
     * @name horizon.app.core.openstack-service-api.nova.getServer
     * @description
     * Get a single server by ID
     * @param {string} id
     * Specifies the id of the server to request.
     */
    function getServer(id) {
      return apiService.get('/api/nova/servers/' + id)
        .error(function () {
          toastService.add('error', gettext('Unable to retrieve the server.'));
        });
    }

    /**
     * @name horizon.app.core.openstack-service-api.nova.getExtensions
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
      return apiService.get('/api/nova/extensions/', config)
        .error(function () {
          toastService.add('error', gettext('Unable to retrieve the extensions.'));
        });
    }

    /**
     * @name horizon.app.core.openstack-service-api.nova.getFlavors
     * @description
     * Returns a list of flavors.
     *
     * The listing result is an object with property "items". Each item is
     * a flavor.
     *
     * @param {boolean} isPublic (optional)
     * True if public flavors should be returned. If not specified, the API
     * will return public flavors by default for Admins and only project
     * flavors for non-admins.
     * @param {boolean} getExtras (optional)
     * Also retrieve the extra specs. This is expensive (one extra underlying
     * call per flavor).
     */
    function getFlavors(isPublic, getExtras) {
      var config = {'params': {}};
      if (isPublic) { config.params.is_public = 'true'; }
      if (getExtras) { config.params.get_extras = 'true'; }
      return apiService.get('/api/nova/flavors/', config)
        .success(function (data) {
          // The colon character ':' in the flavor data causes problems when used
          // in Angular $parse() statements. Since these values are used as keys
          // to lookup data (and may end up in a $parse()) provide "user-friendly"
          // attributes
          if ( data && data.items ) {
            data.items.map(function(item) {
              if ( item.hasOwnProperty('OS-FLV-EXT-DATA:ephemeral')) {
                item.ephemeral = item['OS-FLV-EXT-DATA:ephemeral'];
              }
              if ( item.hasOwnProperty('OS-FLV-DISABLED:disabled')) {
                item.disabled = item['OS-FLV-DISABLED:disabled'];
              }
              if ( item.hasOwnProperty('os-flavor-access:is_public')) {
                item.is_public = item['os-flavor-access:is_public'];
              }
            });
          }
        })
        .error(function () {
          toastService.add('error', gettext('Unable to retrieve the flavors.'));
        });
    }

    /**
     * @name horizon.app.core.openstack-service-api.nova.getFlavor
     * @description
     * Get a single flavor by ID.
     * @param {string} id
     * Specifies the id of the flavor to request.
     * @param {boolean} getExtras (optional)
     * Also retrieve the extra specs for the flavor.
     */
    function getFlavor(id, getExtras) {
      var config = {'params': {}};
      if (getExtras) { config.params.get_extras = 'true'; }
      return apiService.get('/api/nova/flavors/' + id, config)
        .error(function () {
          toastService.add('error', gettext('Unable to retrieve the flavor.'));
        });
    }

    /**
     * @name horizon.app.core.openstack-service-api.nova.getFlavorExtraSpecs
     * @description
     * Get a single flavor's extra specs by ID.
     * @param {string} id
     * Specifies the id of the flavor to request the extra specs.
     */
    function getFlavorExtraSpecs(id) {
      return apiService.get('/api/nova/flavors/' + id + '/extra-specs/')
        .error(function () {
          toastService.add('error', gettext('Unable to retrieve the flavor extra specs.'));
        });
    }

    /**
     * @name horizon.openstack-service-api.nova.editFlavorExtraSpecs
     * @description
     * Update a single flavor's extra specs by ID.
     * @param {string} id
     * @param {object} updated New extra specs.
     * @param {[]} removed Names of removed extra specs.
     */
    function editFlavorExtraSpecs(id, updated, removed) {
      return apiService.patch(
        '/api/nova/flavors/' + id + '/extra-specs/',
        {
          updated: updated,
          removed: removed
        }
      ).error(function () {
        toastService.add('error', gettext('Unable to edit the flavor extra specs.'));
      });
    }

    /**
     * @name horizon.openstack-service-api.nova.getAggregateExtraSpecs
     * @description
     * Get a single aggregate's extra specs by ID.
     * @param {string} id
     * Specifies the id of the flavor to request the extra specs.
     */
    function getAggregateExtraSpecs(id) {
      return apiService.get('/api/nova/aggregates/' + id + '/extra-specs/')
        .error(function () {
          toastService.add('error', gettext('Unable to retrieve the aggregate extra specs.'));
        });
    }

    /**
     * @name horizon.openstack-service-api.nova.editAggregateExtraSpecs
     * @description
     * Update a single aggregate's extra specs by ID.
     * @param {string} id
     * @param {object} updated New extra specs.
     * @param {[]} removed Names of removed extra specs.
     */
    function editAggregateExtraSpecs(id, updated, removed) {
      return apiService.patch(
        '/api/nova/aggregates/' + id + '/extra-specs/',
        {
          updated: updated,
          removed: removed
        }
      ).error(function () {
        toastService.add('error', gettext('Unable to edit the aggregate extra specs.'));
      });
    }
  }

}());
