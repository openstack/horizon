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
(function () {
  'use strict';

  angular
    .module('horizon.app.core.openstack-service-api')
    .service('horizon.app.core.openstack-service-api.nova', NovaAPI);

  NovaAPI.$inject = ['horizon.framework.util.http.service',
                     'horizon.framework.widgets.toast.service'];

  /**
   * @ngdoc service
   * @name horizon.app.core.openstack-service-api.nova
   * @description Provides access to Nova APIs.
   */
  function NovaAPI(apiService, toastService) {

    // Keypairs

    /**
     * @name horizon.app.core.openstack-service-api.nova.getKeypairs
     * @description
     * Get a list of keypairs.
     *
     * The listing result is an object with property "items". Each item is
     * a keypair.
     */
    this.getKeypairs = function() {
      return apiService.get('/api/nova/keypairs/')
        .error(function () {
          toastService.add('error', gettext('Unable to retrieve the keypairs.'));
        });
    };

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
    this.createKeypair = function(newKeypair) {
      return apiService.post('/api/nova/keypairs/', newKeypair)
        .error(function () {
          if (angular.isDefined(newKeypair.public_key)) {
            toastService.add('error', gettext('Unable to import the keypair.'));
          } else {
            toastService.add('error', gettext('Unable to create the keypair.'));
          }
        });
    };

    // Availability Zones

    /**
     * @name horizon.app.core.openstack-service-api.nova.getAvailabilityZones
     * @description
     * Get a list of Availability Zones.
     *
     * The listing result is an object with property "items". Each item is
     * an availability zone.
     */
    this.getAvailabilityZones = function() {
      return apiService.get('/api/nova/availzones/')
        .error(function () {
          toastService.add('error',
                        gettext('Unable to retrieve the availability zones.'));
        });
    };

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
    this.getLimits = function() {
      return apiService.get('/api/nova/limits/')
        .error(function () {
          toastService.add('error', gettext('Unable to retrieve the limits.'));
        });
    };

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
    this.createServer = function(newServer) {
      return apiService.post('/api/nova/servers/', newServer)
        .error(function () {
          toastService.add('error', gettext('Unable to create the server.'));
        });
    };

    /**
     * @name horizon.app.core.openstack-service-api.nova.getServer
     * @description
     * Get a single server by ID
     * @param {string} id
     * Specifies the id of the server to request.
     */
    this.getServer = function(id) {
      return apiService.get('/api/nova/servers/' + id)
        .error(function () {
          toastService.add('error', gettext('Unable to retrieve the server.'));
        });
    };

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
    this.getExtensions = function(config) {
      return apiService.get('/api/nova/extensions/', config)
        .error(function () {
          toastService.add('error', gettext('Unable to retrieve the extensions.'));
        });
    };

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
    this.getFlavors = function(isPublic, getExtras) {
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
    };

    /**
     * @name horizon.app.core.openstack-service-api.nova.getFlavor
     * @description
     * Get a single flavor by ID.
     * @param {string} id
     * Specifies the id of the flavor to request.
     * @param {boolean} getExtras (optional)
     * Also retrieve the extra specs for the flavor.
     */
    this.getFlavor = function(id, getExtras) {
      var config = {'params': {}};
      if (getExtras) { config.params.get_extras = 'true'; }
      return apiService.get('/api/nova/flavors/' + id, config)
        .error(function () {
          toastService.add('error', gettext('Unable to retrieve the flavor.'));
        });
    };

    /**
     * @name horizon.app.core.openstack-service-api.nova.getFlavorExtraSpecs
     * @description
     * Get a single flavor's extra specs by ID.
     * @param {string} id
     * Specifies the id of the flavor to request the extra specs.
     */
    this.getFlavorExtraSpecs = function(id) {
      return apiService.get('/api/nova/flavors/' + id + '/extra-specs')
        .error(function () {
          toastService.add('error', gettext('Unable to retrieve the flavor extra specs.'));
        });
    };
  }

  /**
   * @ngdoc service
   * @name horizon.app.core.openstack-service-api.novaExtensions
   * @description
   * Provides cached access to Nova Extensions with utilities to help
   * with asynchronous data loading. The cache may be reset at any time
   * by accessing the cache and calling removeAll. The next call to any
   * function will retrieve fresh results.
   *
   * The enabled extensions do not change often, so using cached data will
   * speed up results. Even on a local devstack in informal testing,
   * this saved between 30 - 100 ms per request.
   */
  angular
    .module('horizon.app.core.openstack-service-api')
    .factory('horizon.app.core.openstack-service-api.novaExtensions', NovaExtensionsAPI);

  NovaExtensionsAPI.$inject = ['$cacheFactory',
                               '$q',
                               'horizon.app.core.openstack-service-api.nova'];

  function NovaExtensionsAPI($cacheFactory, $q, novaAPI) {
    var service = {};
    service.cache = $cacheFactory('horizon.app.core.openstack-service-api.novaExtensions', {capacity: 1});

    service.get = function () {
      return novaAPI.getExtensions({cache: service.cache})
        .then(function (data) {
          return data.data.items;
        });
    };

    service.ifNameEnabled = function(desired) {
      var deferred = $q.defer();

      service.get().then(onDataLoaded, onDataFailure);

      function onDataLoaded(extensions) {
        if (enabled(extensions, 'name', desired)) {
          deferred.resolve();
        } else {
          deferred.reject(interpolate(
            gettext('Extension is not enabled: %(extension)s.'),
            {extension: desired},
            true));
        }
      }

      function onDataFailure() {
        deferred.reject(gettext('Cannot get the Nova extension list.'));
      }

      return deferred.promise;
    };

    // This is an alias to support the extension directive default interface
    service.ifEnabled = service.ifNameEnabled;

    function enabled(resources, key, desired) {
      if (resources) {
        return resources.some(function (resource) {
          return resource[key] === desired;
        });
      } else {
        return false;
      }
    }

    return service;
  }
}());
