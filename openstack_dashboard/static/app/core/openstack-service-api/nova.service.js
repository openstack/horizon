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
    'horizon.framework.widgets.toast.service'
  ];

  /**
   * @ngdoc service
   * @param {Object} apiService
   * @param {Object} toastService
   * @name novaApi
   * @description Provides access to Nova APIs.
   * @returns {Object} The service
   */
  function novaAPI(apiService, toastService) {

    var service = {
      getActionList: getActionList,
      getConsoleLog: getConsoleLog,
      getConsoleInfo: getConsoleInfo,
      getServerVolumes: getServerVolumes,
      getServerSecurityGroups: getServerSecurityGroups,
      isFeatureSupported: isFeatureSupported,
      getKeypairs: getKeypairs,
      createKeypair: createKeypair,
      getKeypair: getKeypair,
      deleteKeypair: deleteKeypair,
      getAvailabilityZones: getAvailabilityZones,
      getLimits: getLimits,
      createServer: createServer,
      getServer: getServer,
      getServers: getServers,
      getServerGroup: getServerGroup,
      getServerGroups: getServerGroups,
      createServerGroup: createServerGroup,
      deleteServerGroup: deleteServerGroup,
      deleteServer: deleteServer,
      pauseServer: pauseServer,
      unpauseServer: unpauseServer,
      suspendServer: suspendServer,
      resumeServer: resumeServer,
      softRebootServer: softRebootServer,
      hardRebootServer: hardRebootServer,
      startServer: startServer,
      stopServer: stopServer,
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
      createFlavor: createFlavor,
      updateFlavor: updateFlavor,
      deleteFlavor: deleteFlavor,
      getDefaultQuotaSets: getDefaultQuotaSets,
      setDefaultQuotaSets: setDefaultQuotaSets,
      getEditableQuotas: getEditableQuotas,
      updateProjectQuota: updateProjectQuota,
      createServerSnapshot: createServerSnapshot
    };

    return service;

    ///////////

    // Feature

    /**
     * @name isFeatureSupported
     * @description
     * Check if the feature is supported.
     * @returns {Object} The result of the API call
     */
    function isFeatureSupported(feature) {
      return apiService.get('/api/nova/features/' + feature)
        .error(function () {
          toastService.add('error', gettext('Unable to check the Nova service feature.'));
        });
    }

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

    /**
     * @name getKeypair
     * @description
     * Get a single keypair by name.
     *
     * @param {string} name
     * The name of the keypair. Required.
     *
     * @returns {Object} The result of the API call.
     */
    function getKeypair(name) {
      return apiService.get('/api/nova/keypairs/' + name)
        .error(function () {
          toastService.add('error', gettext('Unable to retrieve the keypair.'));
        });
    }

    /**
     * @name deleteKeypair
     * @description
     * Delete a single keypair by name.
     *
     * @param {String} name
     * Keypair to delete
     *
     * @param {boolean} suppressError
     * If passed in, this will not show the default error handling
     * (horizon alert).
     *
     * @returns {Object} The result of the API call
     */
    function deleteKeypair(name, suppressError) {
      var promise = apiService.delete('/api/nova/keypairs/' + name);
      return suppressError ? promise : promise.error(function() {
        var msg = gettext('Unable to delete the keypair with name: %(name)s');
        toastService.add('error', interpolate(msg, { name: name }, true));
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
    function getLimits(reserved) {
      var params = { params: {reserved: reserved }};
      return apiService.get('/api/nova/limits/', params)
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
     * @name getServerGroup
     * @description
     * Get a single server group by ID
     * @param {string} id
     * Specifies the id of the server group to request.
     * @returns {Object} The result of the API call
     */
    function getServerGroup(id) {
      return apiService.get('/api/nova/servergroups/' + id)
        .error(function () {
          toastService.add('error', gettext('Unable to retrieve the server group.'));
        });
    }

    /**
     * @name getServerGroups
     * @description
     * Get a list of server groups.
     *
     * The listing result is an object with property "items". Each item is
     * a server group.
     * @returns {Object} The result of the API call
     */
    function getServerGroups() {
      return apiService.get('/api/nova/servergroups/')
        .error(function () {
          toastService.add('error', gettext('Unable to retrieve server groups.'));
        });
    }

    /**
     * @name createServerGroup
     * @description
     * Create a new server group. This returns the new server group object on success.
     *
     * @param {Object} newServerGroup
     * The server group to create.
     *
     * @param {string} newServerGroup.name
     * The name of the new server group. Required.
     *
     * @param {array} newServerGroup.policies
     * The policies of the new server group. Required.
     * @returns {Object} The result of the API call
     */
    function createServerGroup(newServerGroup) {
      return apiService.post('/api/nova/servergroups/', newServerGroup)
        .error(function () {
          toastService.add('error', gettext('Unable to create the server group.'));
        });
    }

    /**
     * @name deleteServerGroup
     * @description
     * Delete a single server group by ID.
     *
     * @param {String} serverGroupId
     * Server Group to delete
     *
     * @param {boolean} suppressError
     * If passed in, this will not show the default error handling
     * (horizon alert).
     *
     * @returns {Object} The result of the API call
     */
    function deleteServerGroup(serverGroupId, suppressError) {
      var promise = apiService.delete('/api/nova/servergroups/' + serverGroupId + '/');
      return suppressError ? promise : promise.error(function() {
        var msg = gettext('Unable to delete the server group with id %(id)s');
        toastService.add('error', interpolate(msg, { id: serverGroupId }, true));
      });
    }

    /*
     * @name deleteServer
     * @description
     * Delete a single server by ID.
     *
     * @param {String} serverId
     * Server to delete
     * @returns {Object} The result of the API call
     */
    function deleteServer(serverId, suppressError) {
      var promise = apiService.delete('/api/nova/servers/' + serverId);

      return suppressError ? promise : promise.error(function() {
        var msg = gettext('Unable to delete the server with id: %(id)s');
        toastService.add('error', interpolate(msg, { id: serverId }, true));
      });
    }

    function serverStateOperation(operation, serverId, suppressError, errMsg) {
      var instruction = {"operation": operation};
      var promise = apiService.post('/api/nova/servers/' + serverId, instruction);

      return suppressError ? promise : promise.error(function() {
        toastService.add('error', interpolate(errMsg, { id: serverId }, true));
      });

    }

    /**
     * @name startServer
     * @description
     * Start a single server by ID.
     *
     * @param {String} serverId
     * Server to start
     * @returns {Object} The result of the API call
     */
    function startServer(serverId, suppressError) {
      return serverStateOperation('start', serverId, suppressError,
        gettext('Unable to start the server with id: %(id)s'));
    }

    /**
     * @name pauseServer
     * @description
     * Pause a single server by ID.
     *
     * @param {String} serverId
     * Server to pause
     * @returns {Object} The result of the API call
     */
    function pauseServer(serverId, suppressError) {
      return serverStateOperation('pause', serverId, suppressError,
        gettext('Unable to pause the server with id: %(id)s'));
    }

    /**
     * @name unpauseServer
     * @description
     * Un-Pause a single server by ID.
     *
     * @param {String} serverId
     * Server to unpause
     * @returns {Object} The result of the API call
     */
    function unpauseServer(serverId, suppressError) {
      return serverStateOperation('unpause', serverId, suppressError,
        gettext('Unable to unpause the server with id: %(id)s'));
    }

    /**
     * @name suspendServer
     * @description
     * Suspend a single server by ID.
     *
     * @param {String} serverId
     * Server to suspend
     * @returns {Object} The result of the API call
     */
    function suspendServer(serverId, suppressError) {
      return serverStateOperation('suspend', serverId, suppressError,
        gettext('Unable to suspend the server with id: %(id)s'));
    }

    /**
     * @name resumeServer
     * @description
     * Resumes a single server by ID.
     *
     * @param {String} serverId
     * Server to resume
     * @returns {Object} The result of the API call
     */
    function resumeServer(serverId, suppressError) {
      return serverStateOperation('resume', serverId, suppressError,
        gettext('Unable to resume the server with id: %(id)s'));
    }

    /**
     * @name softRebootServer
     * @description
     * Soft-reboots a single server by ID.
     *
     * @param {String} serverId
     * Server to reboot
     * @returns {Object} The result of the API call
     */
    function softRebootServer(serverId, suppressError) {
      return serverStateOperation('soft_reboot', serverId, suppressError,
        gettext('Unable to soft-reboot the server with id: %(id)s'));
    }

    /**
     * @name hardRebootServer
     * @description
     * Hard-reboots a single server by ID.
     *
     * @param {String} serverId
     * Server to reboot
     * @returns {Object} The result of the API call
     */
    function hardRebootServer(serverId, suppressError) {
      return serverStateOperation('hard_reboot', serverId, suppressError,
        gettext('Unable to hard-reboot the server with id: %(id)s'));
    }

    /**
     * @name stopServer
     * @description
     * Stop a single server by ID.
     *
     * @param {String} serverId
     * Server to stop
     * @returns {Object} The result of the API call
     */
    function stopServer(serverId, suppressError) {
      return serverStateOperation('stop', serverId, suppressError,
        gettext('Unable to stop the server with id: %(id)s'));
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
     * @param {Object} params (optional)
     * Parameters that should be passed to the API call. Currently those can
     * be "is_public" and "get_extras", both of them boolean.
     * @returns {Object} The result of the API call
     */
    function getFlavors(params) {
      var config = params ? { 'params' : params} : { 'params' : {} };
      return apiService.get('/api/nova/flavors/', config)
        .success(function (data) {
          // The colon character ':' in the flavor data causes problems when used
          // in Angular $parse() statements. Since these values are used as keys
          // to lookup data (and may end up in a $parse()) provide "user-friendly"
          // attributes
          if (data && data.items) {
            data.items.map(function(item) {
              if (item.hasOwnProperty('OS-FLV-EXT-DATA:ephemeral')) {
                item.ephemeral = item['OS-FLV-EXT-DATA:ephemeral'];
              }
              if (item.hasOwnProperty('OS-FLV-DISABLED:disabled')) {
                item.disabled = item['OS-FLV-DISABLED:disabled'];
              }
              if (item.hasOwnProperty('os-flavor-access:is_public')) {
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

    // Default Quota Sets

    /**
     * @name getDefaultQuotaSets
     * @description
     * Get default quotasets
     *
     * The listing result is an object with property "items." Each item is
     * a quota.
     *
     */
    function getDefaultQuotaSets() {
      return apiService.get('/api/nova/quota-sets/defaults/')
        .error(function () {
          toastService.add('error', gettext('Unable to retrieve the default quotas.'));
        });
    }

    /**
     * @name setDefaultQuotaSets
     * @description
     * Set default quotasets
     *
     */
    function setDefaultQuotaSets(quotas) {
      return apiService.patch('/api/nova/quota-sets/defaults/', quotas)
        .error(function () {
          toastService.add('error', gettext('Unable to set the default quotas.'));
        });
    }

    // Quota Sets

    /**
     * @name getEditableQuotas
     * @description
     * Get a list of editable quota fields.
     * The listing result is an object with property "items." Each item is
     * an editable quota field.
     *
     */
    function getEditableQuotas() {
      return apiService.get('/api/nova/quota-sets/editable/')
        .error(function() {
          toastService.add('error', gettext('Unable to retrieve the editable quotas.'));
        });
    }

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
      var url = '/api/nova/quota-sets/' + projectId;
      return apiService.patch(url, quota)
        .error(function() {
          toastService.add('error', gettext('Unable to update project quota data.'));
        });
    }

    /**
     * @name createServerSnapshot
     * @param {Object} newSnapshot - The new server snapshot
     * @description
     * Create a server snapshot using the parameters supplied in the
     * newSnapshot. The required parameters:
     *
     * "name", "instance_id"
     *     All strings
     *
     * @returns {Object} The result of the API call
     */
    function createServerSnapshot(newSnapshot) {
      return apiService.post('/api/nova/snapshots/', newSnapshot)
        .error(function () {
          toastService.add('error', gettext('Unable to create the server snapshot.'));
        });
    }

    /**
     * @name getActionList
     * @param {String} ID - The server ID
     * @description
     * Retrieves a list of actions performed on the server.
     *
     * @returns {Object} The result of the API call
     */
    function getActionList(instanceId) {
      return apiService.get('/api/nova/servers/' + instanceId + '/actions/')
        .error(function () {
          toastService.add('error', gettext('Unable to load the server actions.'));
        });
    }

    /**
     * @name getConsoleLog
     * @param {String} instanceId - The server ID
     * @param {Number} length - The number of lines to retrieve (optional)
     * @description
     * Retrieves a list of most recent console log lines from the server.
     *
     * @returns {Object} The result of the API call
     */
    function getConsoleLog(instanceId, length) {
      var config = {};
      if (length) {
        config.length = length;
      }
      return apiService.post('/api/nova/servers/' + instanceId + '/console-output/', config)
        .error(function () {
          toastService.add('error', gettext('Unable to load the server console log.'));
        });
    }

    /**
     * @name getConsoleInfo
     * @param {String} instanceId - The server ID
     * @param {String} type - The type of console to use (optional)
     * @description
     * Retrieves information used to get to a remote console for the given host.
     *
     * @returns {Object} The result of the API call
     */
    function getConsoleInfo(instanceId, type) {
      var config = {};
      if (type) {
        config.console_type = type;
      }
      return apiService.post('/api/nova/servers/' + instanceId + '/console-info/', config)
        .error(function () {
          toastService.add('error', gettext('Unable to load the server console info.'));
        });
    }

    /**
     * @name getServerVolumes
     * @param {String} instanceId - The server ID
     * @description
     * Retrieves information about volumes associated with the server
     *
     * @returns {Object} The result of the API call
     */
    function getServerVolumes(instanceId) {
      return apiService.get('/api/nova/servers/' + instanceId + '/volumes/')
        .error(function () {
          toastService.add('error', gettext('Unable to load the server volumes.'));
        });
    }

    /**
     * @name getServerSecurityGroups
     * @param {String} ID - The server ID
     * @description
     * Retrieves information about security groups associated with the server
     *
     * @returns {Object} The result of the API call
     */
    function getServerSecurityGroups(instanceId) {
      return apiService.get('/api/nova/servers/' + instanceId + '/security-groups/')
        .error(function () {
          toastService.add('error', gettext('Unable to load the server security groups.'));
        });
    }

  }
}());
