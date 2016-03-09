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
    .factory('horizon.app.core.openstack-service-api.nova', novaAPI);

  novaAPI.$inject = [
    'horizon.framework.util.http.service',
    'horizon.framework.widgets.toast.service',
    '$window'
  ];

  /**
   * @ngdoc service
   * @param {Object} apiService
   * @param {Object} toastService
   * @param {Object} $window
   * @name novaApi
   * @description Provides access to Nova APIs.
   * @returns {Object} The service
   */
  function novaAPI(apiService, toastService, $window) {

    var service = {
      getKeypairs: getKeypairs,
      createKeypair: createKeypair,
      getAvailabilityZones: getAvailabilityZones,
      getLimits: getLimits,
      createServer: createServer,
      getServer: getServer,
      getServers: getServers,
      getExtensions: getExtensions,
      getFlavors: getFlavors,
      getFlavor: getFlavor,
      getFlavorExtraSpecs: getFlavorExtraSpecs,
      editFlavorExtraSpecs: editFlavorExtraSpecs,
      getAggregateExtraSpecs: getAggregateExtraSpecs,
      editAggregateExtraSpecs: editAggregateExtraSpecs,
      getServices: getServices,
      getInstanceMetadata: getInstanceMetadata,
      editInstanceMetadata: editInstanceMetadata,
      getCreateKeypairUrl: getCreateKeypairUrl,
      getRegenerateKeypairUrl: getRegenerateKeypairUrl,
      createFlavor: createFlavor,
      updateFlavor: updateFlavor,
      deleteFlavor: deleteFlavor
    };

    return service;

    ///////////

    // Nova Services

    /**
     * @name getServices
     * @description Get the list of Nova services.
     *
     * @returns {Object} The listing result is an object with property "services." Each item is
     * a service.
     */
    function getServices() {
      return apiService.get('/api/nova/services/')
        .error(function () {
          toastService.add('error', gettext('Unable to retrieve the nova services.'));
        });
    }

    // Keypairs

    /**
     * @name getKeypairs
     * @description
     * Get a list of keypairs.
     *
     * @returns {Object} An object with property "items". Each item is a keypair.
     */
    function getKeypairs() {
      return apiService.get('/api/nova/keypairs/')
        .error(function () {
          toastService.add('error', gettext('Unable to retrieve the keypairs.'));
        });
    }

    /**
     * @name createKeypair
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
     * @returns {Object} The result of the API call
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
     * @name getAvailabilityZones
     * @description
     * Get a list of Availability Zones.
     *
     * The listing result is an object with property "items". Each item is
     * an availability zone.
     * @returns {Object} The result of the API call
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
     * @name getLimits
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
     * @returns {Object} The result of the API call
     */
    function getLimits() {
      return apiService.get('/api/nova/limits/')
        .error(function () {
          toastService.add('error', gettext('Unable to retrieve the limits.'));
        });
    }

    // Servers

    /**
     * @name createServer
     * @param {Object} newServer - The new server
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
     * @returns {Object} The result of the API call
     */
    function createServer(newServer) {
      return apiService.post('/api/nova/servers/', newServer)
        .error(function () {
          toastService.add('error', gettext('Unable to create the server.'));
        });
    }

    /**
     * @name getServer
     * @description
     * Get a single server by ID
     * @param {string} id
     * Specifies the id of the server to request.
     * @returns {Object} The result of the API call
     */
    function getServer(id) {
      return apiService.get('/api/nova/servers/' + id)
        .error(function () {
          toastService.add('error', gettext('Unable to retrieve the server.'));
        });
    }

    /**
     * @name getServers
     * @description
     * Get a list of servers.
     *
     * The listing result is an object with property "items". Each item is
     * a server.
     * @returns {Object} The result of the API call
     */
    function getServers() {
      return apiService.get('/api/nova/servers/')
        .error(function () {
          toastService.add('error', gettext('Unable to retrieve instances.'));
        });
    }

    /**
     * @name getExtensions
     * @param {Object} config - A configuration object
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
     * @returns {Object} The list of enable extensions
     */
    function getExtensions(config) {
      return apiService.get('/api/nova/extensions/', config)
        .error(function () {
          toastService.add('error', gettext('Unable to retrieve the extensions.'));
        });
    }

    /**
     * @name getFlavors
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
     * @returns {Object} The result of the API call
     */
    function getFlavors(isPublic, getExtras) {
      var config = {'params': {}};
      if (isPublic) {
        config.params.is_public = 'true';
      }
      if (getExtras) {
        config.params.get_extras = 'true';
      }
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
     * @name getFlavor
     * @description
     * Get a single flavor by ID.
     * @param {string} id
     * Specifies the id of the flavor to request.
     * @param {boolean} getExtras (optional)
     * Also retrieve the extra specs for the flavor.
     * @param {boolean} getAccessList - True if you want get the access list
     * @returns {Object} The result of the API call
     */
    function getFlavor(id, getExtras, getAccessList) {
      var config = {'params': {}};
      if (getExtras) {
        config.params.get_extras = 'true';
      }
      if (getAccessList) {
        config.params.get_access_list = 'true';
      }
      return apiService.get('/api/nova/flavors/' + id + '/' , config)
        .error(function () {
          toastService.add('error', gettext('Unable to retrieve the flavor.'));
        });
    }

    /**
     * @name createFlavor
     * @description
     * Create a single flavor.
     * @param {flavor} flavor
     * Flavor to create
     * @returns {Object} The result of the API call
     */
    function createFlavor(flavor) {
      return apiService.post('/api/nova/flavors/', flavor)
        .error(function () {
          toastService.add('error', gettext('Unable to create the flavor.'));
        });
    }

    /**
     * @name updateFlavor
     * @description
     * Update a single flavor.
     * @param {flavor} flavor
     * Flavor to update
     * @returns {Object} The result of the API call
     */
    function updateFlavor(flavor) {
      return apiService.patch('/api/nova/flavors/' + flavor.id + '/', flavor)
        .error(function () {
          toastService.add('error', gettext('Unable to update the flavor.'));
        });
    }

    /**
     * @name deleteFlavor
     * @description
     * Delete a single flavor by ID.
     *
     * @param {String} flavorId
     * Flavor to delete
     *
     * @param {boolean} suppressError
     * If passed in, this will not show the default error handling
     * (horizon alert). The glance API may not have metadata definitions
     * enabled.
     * @returns {Object} The result of the API call
     */
    function deleteFlavor(flavorId, suppressError) {
      var promise = apiService.delete('/api/nova/flavors/' + flavorId + '/');

      return suppressError ? promise : promise.error(function() {
        var msg = gettext('Unable to delete the flavor with id: %(id)s');
        toastService.add('error', interpolate(msg, { id: flavorId }, true));
      });

    }

    /**
     * @name getFlavorExtraSpecs
     * @description
     * Get a single flavor's extra specs by ID.
     * @param {string} id
     * Specifies the id of the flavor to request the extra specs.
     * @returns {Object} The result of the API call
     */
    function getFlavorExtraSpecs(id) {
      return apiService.get('/api/nova/flavors/' + id + '/extra-specs/')
        .error(function () {
          toastService.add('error', gettext('Unable to retrieve the flavor extra specs.'));
        });
    }

    /**
     * @name editFlavorExtraSpecs
     * @description
     * Update a single flavor's extra specs by ID.
     * @param {string} id
     * @param {object} updated New extra specs.
     * @param {[]} removed Names of removed extra specs.
     * @returns {Object} The result of the API call
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
     * @name getAggregateExtraSpecs
     * @description
     * Get a single aggregate's extra specs by ID.
     * @param {string} id
     * Specifies the id of the flavor to request the extra specs.
     * @returns {Object} The result of the API call
     */
    function getAggregateExtraSpecs(id) {
      return apiService.get('/api/nova/aggregates/' + id + '/extra-specs/')
        .error(function () {
          toastService.add('error', gettext('Unable to retrieve the aggregate extra specs.'));
        });
    }

    /**
     * @name editAggregateExtraSpecs
     * @description
     * Update a single aggregate's extra specs by ID.
     * @param {string} id
     * @param {object} updated New extra specs.
     * @param {[]} removed Names of removed extra specs.
     * @returns {Object} The result of the API call
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

    /**
     * @name getInstanceMetadata
     * @description
     * Get a single instance's metadata by ID.
     * @param {string} id
     * Specifies the id of the instance to request the metadata.
     * @returns {Object} The result of the API call
     */
    function getInstanceMetadata(id) {
      return apiService.get('/api/nova/servers/' + id + '/metadata')
        .error(function () {
          toastService.add('error', gettext('Unable to retrieve instance metadata.'));
        });
    }

    /**
     * @name editInstanceMetadata
     * @description
     * Update a single instance's metadata by ID.
     * @param {string} id
     * @param {object} updated New metadata.
     * @param {[]} removed Names of removed metadata items.
     * @returns {Object} The result of the API call
     */
    function editInstanceMetadata(id, updated, removed) {
      return apiService.patch(
        '/api/nova/servers/' + id + '/metadata',
        {
          updated: updated,
          removed: removed
        }
      ).error(function () {
        toastService.add('error', gettext('Unable to edit instance metadata.'));
      });
    }

    /**
     * @ngdoc function
     * @name getCreateKeypairUrl
     *
     * @description
     * Returns a URL, respecting WEBROOT, that if called as a REST call
     * would create and return a new key pair with the given name.  This
     * function is provided because to perform a download of the key pair,
     * an iframe must be given a URL to use (which is further explained in
     * the key pair download service).
     *
     * @param {string} keyPairName
     * @returns {Object} The result of the API call
     */
    function getCreateKeypairUrl(keyPairName) {
      // NOTE: WEBROOT by definition must end with a slash (local_settings.py).
      return $window.WEBROOT + "api/nova/keypairs/" +
        encodeURIComponent(keyPairName) + "/";
    }

    /**
     * @ngdoc function
     * @name getRegenerateKeypairUrl
     *
     * @description
     * Returns a URL, respecting WEBROOT, that if called as a REST call
     * would regenereate an existing key pair with the given name and return
     * the new key pair data.  This function is provided because to perform
     * a download of the key pair, an iframe must be given a URL to use
     * (which is further explained in the key pair download service).
     *
     * @param {string} keyPairName
     * @returns {Object} The result of the API call
     */
    function getRegenerateKeypairUrl(keyPairName) {
      return getCreateKeypairUrl(keyPairName) + "?regenerate=true";
    }

  }
}());
