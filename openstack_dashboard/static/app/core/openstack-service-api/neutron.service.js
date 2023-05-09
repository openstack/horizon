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

  angular
    .module('horizon.app.core.openstack-service-api')
    .factory('horizon.app.core.openstack-service-api.neutron', neutronAPI);

  neutronAPI.$inject = [
    'horizon.framework.util.http.service',
    'horizon.framework.widgets.toast.service'
  ];

  /**
   * @ngdoc service
   * @name neutronAPI
   * @param {Object} apiService
   * @param {Object} toastService
   * @description Provides access to Neutron APIs.
   * @returns {Object} The service
   */
  function neutronAPI(apiService, toastService) {
    var service = {
      createNetwork: createNetwork,
      createSubnet: createSubnet,
      createTrunk: createTrunk,
      createNetworkQoSPolicy: createNetworkQoSPolicy,
      createBandwidthLimitRule: createBandwidthLimitRule,
      createDSCPMarkingRule: createDSCPMarkingRule,
      createMinimumBandwidthRule: createMinimumBandwidthRule,
      createMinimumPacketRateRule: createMinimumPacketRateRule,
      deletePolicy: deletePolicy,
      deleteTrunk: deleteTrunk,
      getAgents: getAgents,
      getDefaultQuotaSets: getDefaultQuotaSets,
      getExtensions: getExtensions,
      getNetworks: getNetworks,
      getPorts: getPorts,
      getQosPolicy: getQosPolicy,
      getQoSPolicies: getQoSPolicies,
      getSubnets: getSubnets,
      getTrunk: getTrunk,
      getTrunks: getTrunks,
      updateProjectQuota: updateProjectQuota,
      updateTrunk: updateTrunk,
      deleteDSCPMarkingRule: deleteDSCPMarkingRule,
      deleteBandwidthLimitRule: deleteBandwidthLimitRule,
      deleteMinimumBandwidthRule: deleteMinimumBandwidthRule,
      deleteMinimumPacketRateRule: deleteMinimumPacketRateRule,
      updateMinimumBandwidthRule: updateMinimumBandwidthRule,
      updateDSCPMarkingRule: updateDSCPMarkingRule,
      updateBandwidthRule: updateBandwidthRule,
      updateMinimumPacketRateRule: updateMinimumPacketRateRule
    };

    return service;

    /////////////

    // NOTE(bence romsics): Technically we replace ISO 8061 time stamps with
    // date objects. We do this because the date objects will stringify to human
    // readable datetimes in local time (ie. in the browser's time zone) when
    // displayed.
    function convertDatesHumanReadable(apidict) {
      apidict.created_at = new Date(apidict.created_at);
      apidict.updated_at = new Date(apidict.updated_at);
    }

    // Neutron Services

    /**
     * @name getAgents
     * @description Get the list of Neutron agents.
     *
     * @returns {Object} An object with property "items." Each item is an agent.
     */
    function getAgents() {
      return apiService.get('/api/neutron/agents/')
        .catch(function onError() {
          toastService.add('error', gettext('Unable to retrieve the agents.'));
        });
    }

    // Networks

    /**
     * @name getNetworks
     * @description
     * Get a list of networks for a tenant.
     *
     * @returns {Object} An object with property "items". Each item is a network.
     */
    function getNetworks() {
      return apiService.get('/api/neutron/networks/')
        .catch(function onError() {
          toastService.add('error', gettext('Unable to retrieve the networks.'));
        });
    }

    /**
     * @name createNetwork
     * @description
     * Create a new network.
     * @returns {Object} The new network object on success.
     *
     * @param {Object} newNetwork
     * The network to create.  Required.
     *
     * Example new network object
     * {
     *    "name": "myNewNetwork",
     *    "admin_state_up": true,
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
    function createNetwork(newNetwork) {
      return apiService.post('/api/neutron/networks/', newNetwork)
        .catch(function onError() {
          toastService.add('error', gettext('Unable to create the network.'));
        });
    }

    // Subnets

    /**
     * @name getSubnets
     * @description
     * Get a list of subnets for a network.
     *
     * The listing result is an object with property "items". Each item is
     * a subnet.
     *
     * @param {string} networkId
     * The network id to retrieve subnets for. Required.
     * @returns {Object} The result of the API call
     */
    function getSubnets(networkId) {
      return apiService.get('/api/neutron/subnets/', networkId)
        .catch(function onError() {
          toastService.add('error', gettext('Unable to retrieve the subnets.'));
        });
    }

    /**
     * @name createSubnet
     * @description
     * Create a Subnet for given Network.
     * @returns {Object} The JSON representation of Subnet on success.
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
    function createSubnet(newSubnet) {
      return apiService.post('/api/neutron/subnets/', newSubnet)
        .catch(function onError() {
          toastService.add('error', gettext('Unable to create the subnet.'));
        });
    }

    // Ports

    /**
     * @name getPorts
     * @description
     * Get a list of ports for a network.
     *
     * The listing result is an object with property "items". Each item is
     * a port.
     *
     * @param {string} params - The parameters
     * @param {string} params.status
     * The port status. Value is ACTIVE or DOWN.
     *
     * @param {string} params.display_name
     * The port name.
     *
     * @param {boolean} params.admin_state
     * The administrative state of the router, which is up (true) or down (false).
     *
     * @param {string} params.network_id
     * The UUID of the attached network.
     *
     * @param {string} params.tenant_id
     * The UUID of the tenant who owns the network.
     * Only administrative users can specify a tenant UUID other than their own.
     * You cannot change this value through authorization policies.
     *
     * @param {string} params.device_owner
     * The UUID of the entity that uses this port. For example, a DHCP agent.
     *
     * @param {string} params.mac_address
     * The MAC address of the port.
     *
     * @param {string} params.port_id
     * The UUID of the port.
     *
     * @param {Array} params.security_groups
     * The UUIDs of any attached security groups.
     *
     * @param {string} params.device_id
     * The UUID of the device that uses this port. For example, a virtual server.
     *
     * @returns {Object} The result of the API call
     */
    function getPorts(params) {
      var config = params ? { 'params' : params} : {};
      return apiService.get('/api/neutron/ports/', config)
        .catch(function onError() {
          toastService.add('error', gettext('Unable to retrieve the ports.'));
        });
    }

    // Extensions

    /**
     * @name getExtensions
     * @description
     * Returns a list of enabled extensions.
     *
     * The listing result is an object with property "items". Each item is
     * an extension.
     * @example
     * The following is an example of response:
     *
     *  {
     *    "items": [
     *      {
     *        "updated": "2012-07-29T10:00:00-00:00",
     *        "name": "Quota management support",
     *        "links": [],
     *        "alias": "quotas",
     *        "description": "Expose functions for quotas management per tenant"
     *      }
     *    ]
     *  }
     * @returns {Object} The result of the API call
     */
    function getExtensions() {
      return apiService.get('/api/neutron/extensions/')
        .catch(function onError() {
          toastService.add('error', gettext('Unable to retrieve the extensions.'));
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
      return apiService.get('/api/neutron/quota-sets/defaults/')
        .catch(function onError() {
          toastService.add('error', gettext('Unable to retrieve the default quotas.'));
        });
    }

    // Quotas Extension

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
      var url = '/api/neutron/quotas-sets/' + projectId;
      return apiService.patch(url, quota)
        .catch(function onError() {
          toastService.add('error', gettext('Unable to update project quota data.'));
        });
    }

    // QoS policies

    /**
     * @name horizon.app.core.openstack-service-api.neutron.getQosPolicy
     * @description get a single qos policy by ID.
     * @param {string} id
     * Specifies the id of the policy to request.
     * @returns {Object} The result of the API call
     */
    function getQosPolicy(id, suppressError) {
      var promise = apiService.get('/api/neutron/qos_policies/' + id + '/')
        .then(function onSuccess(response) {
          convertDatesHumanReadable(response.data);
          return response;
        });
      promise = suppressError ? promise : promise.catch(function onError() {
        var msg = gettext('Unable to retrieve the policy with ID %(id)s');
        toastService.add('error', interpolate(msg, {id: id}, true));
      });
      return promise;
    }

    /**
     * @name horizon.app.core.openstack-service-api.neutron.getQoSPolicies
     * @description get a list of qos policies.
     *
     * The listing result is an object with property "items". Each item is
     * a QoS policy.
     */
    function getQoSPolicies(params) {
      var config = params ? {'params' : params} : {};
      return apiService.get('/api/neutron/qos_policies/', config)
        .then(function onSuccess(response) {
          response.data.items.forEach(function(policy) {
            convertDatesHumanReadable(policy);
          });
          return response;
        })
        .catch(function onError() {
          toastService.add('error', gettext('Unable to retrieve the qos policies.'));
        });
    }

     /**
     * @name createNetworkQoSPolicy
     * @description
     * Create a new network qos policy.
     * @returns {Object} The new network qos policy object on success.
     *
     * @param {Object} newQosPolicy
     * The network qos policy to create.  Required.
     *
     * Example new qos policy object
     * {
     *    "name": "myNewNetworkQoSPolicy",
     *    "description": "new network qos policy",
     *    "shared": true,
     * }
     *
     * Description of properties on the qos policy object
     *
     * @property {string} newQosPolicy.name
     * The name of the new network qos policy. Required.
     *
     * @property {string} newQosPolicy.description
     * The description of the qos policy. Optional.
     *
     * @property {boolean} newQosPolicy.shared
     * Indicates whether this network qos policy is shared across all other projects.
     * By default, it is unchecked (false). Optional.
     *
     */
    function createNetworkQoSPolicy(newQosPolicy) {
      return apiService.post('/api/neutron/qos_policies/', newQosPolicy)
        .catch(function onError() {
          toastService.add('error', gettext('Unable to create the QoS Policy.'));
        });
    }

   /**
    * @name deletePolicy
    * @description
    * Delete a single neutron qos policy.
    * @param {string} policyId
    * Specifies the id of the policy to be deleted.
    */
    function deletePolicy(policyId, suppressError) {
      var promise = apiService.delete('/api/neutron/qos_policies/' + policyId + '/');
      promise = suppressError ? promise : promise.catch(function onError() {
        var msg = gettext('Unable to delete qos policy %(id)s');
        toastService.add('error', interpolate(msg, { id: policyId }, true));
      });
      return promise;
    }

    /**
     * @name createBandwidthLimitRule
     * @description
     * Creates a bandwidth limit rule for a QoS policy
     * @returns {Object} A bandwidth_limit_rule object on success.
     *
     * @param {Object} policyId
     * This param is for qos policy.
     *
     * @param {Object} ruleId
     * The bandwidth limit rule to create. Required.
     *
     * Example new bandwidth limit rule response object
     * {
     *   "bandwidth_limit_rule": {
     *     "id": "5f126d84-551a-4dcf-bb01-0e9c0df0c793",
     *      "max_kbps": 10000,
     *      "max_burst_kbps": 0,
     *      "direction": "egress"
     *    }
     * }
     *
     * Description of properties on the bandwidth limit rule object
     *
     * @property {integer} ruleId.max_kbps
     * The maximum KBPS (kilobits per second) value.
     * If you specify this value, must be greater than '0'
     * otherwise max_kbps will have no value. Required.
     *
     * @property {integer} ruleId.max_burst_kbps
     * The maximum burst size (in kilobits). Default is '0'. Optional.
     *
     * @property {string} ruleId.direction
     * The direction of the traffic to which the QoS rule is applied,
     * as seen from the point of view of the port.
     * Valid values are egress and ingress. Default value is egress.
     * Optional.
     *
     */
    function createBandwidthLimitRule(policyId, ruleId) {
      return apiService.post('/api/neutron/qos/policies/' + policyId +
             '/bandwidth_limit_rules/', ruleId)
       .catch(function onError() {
         toastService.add('error', gettext('Unable to add the bandwidthrule .'));
       });
    }

    /**
     * @name createDSCPMarkingRule
     * @description
     * Creates a DSCP marking rule for a QoS policy.
     * @returns {Object} A dscp_marking_rule object on success.
     *
     * @param {Object} policyId
     * This param is for qos policy.
     *
     * @param {Object} ruleId
     * The dscp marking rule to create. Required.
     *
     * Example new dscp mark rule response object
     * {
     *   "dscp_marking_rule": {
     *      "id": "5f126d84-551a-4dcf-bb01-0e9c0df0c794",
     *      "dscp_mark": 26
     *    }
     * }
     *
     * Description of properties on the dscp marking rule object
     *
     * @property {integer} ruleId.dscp_mark
     * The DSCP mark value. Required.
     * Valid DSCP mark values are even numbers between 0 and 56,
     * except 2-6, 42, 44, and 50-54. The full list of valid DSCP marks is:
     * 0, 8, 10, 12, 14, 16, 18, 20, 22, 24, 26, 28, 30, 32, 34, 36, 38, 40, 46, 48, 56
     *
     */
    function createDSCPMarkingRule(policyId, ruleId) {
      return apiService.post('/api/neutron/qos/policies/' + policyId +
             '/dscp_marking_rules/', ruleId)
       .catch(function onError() {
         toastService.add('error', gettext('Unable to add the dscp_marking_rule .'));
       });
    }

    /**
     * @name createMinimumBandwidthRule
     * @description
     * Creates a minimum bandwidth rule for a QoS policy
     * @returns {Object} A minimum_bandwidth_rule object on success.
     *
     * @param {Object} policyId
     * This param is for qos policy.
     *
     * @param {Object} ruleId
     * The minimum bandwidth rule to create.  Required.
     *
     * Example new minimum bandwidth rule response object
     * {
     *   "minimum_bandwidth_rule": {
     *      "id": "1eddf7af-0b4c-42c5-8ae1-390b32f1de08",
     *      "min_kbps": 10000,
     *      "direction": "egress"
     *    }
     * }
     *
     * Description of properties on the minimum bandwidth rule object
     *
     * @property {integer} ruleId.min_kbps
     * The minimum KBPS (kilobits per second) value which should be available for port.
     * Required.
     *
     * @property {string} ruleId.direction
     * The direction of the traffic to which the QoS rule is applied,
     * as seen from the point of view of the port.
     * Valid values are egress and ingress. Default value is egress.
     * Optional.
     *
     */
    function createMinimumBandwidthRule(policyId, ruleId) {
      return apiService.post('/api/neutron/qos/policies/' + policyId +
             '/minimum_bandwidth_rules/', ruleId)
       .catch(function onError() {
         toastService.add('error', gettext('Unable to add the minimum_bandwidth_rule .'));
       });
    }

    /**
     * @name createMinimumPacketRateRule
     * @description
     * Creates a minimum packet rate rule for a QoS policy
     * @returns {Object} A minimum_bandwidth_rule object on success.
     *
     * @param {Object} policyId
     * This param is for qos policy.
     *
     * @param {Object} ruleId
     * The minimum packet rate rule to create.  Required.
     *
     * Example new minimum packet rate rule response object
     * {
     *   "minimum_packet_rate_rule": {
     *      "id": "1eddf7af-0b4c-42c5-8ae1-390b32f1de08",
     *      "min_kpps": 10000,
     *      "direction": "egress"
     *    }
     * }
     *
     * Description of properties on the minimum packet rate rule object
     *
     * @property {integer} ruleId.min_kbps
     * The minimum kpps (kilo(1000) packets per second) value which should be available for port.
     * Required.
     *
     * @property {string} ruleId.direction
     * The direction of the traffic to which the QoS rule is applied,
     * as seen from the point of view of the port.
     * Valid values are egress and ingress. Default value is egress.
     * Optional.
     *
     */
    function createMinimumPacketRateRule(policyId, ruleId) {
      return apiService.post('/api/neutron/qos/policies/' + policyId +
              '/minimum_packet_rate_rules/', ruleId)
        .catch(function onError() {
          toastService.add('error', gettext('Unable to add the minimum_packet_rate_rule.'));
        });
    }

    /**
     * @name updateBandwidthRule
     * @description
     * Update an existing bandwidth limit rule for a QoS policy.
     * @returns {Object} A bandwidth_limit_rule object on success.
     *
     * @param {Object} policyId
     * This param is for qos policy.
     *
     * @param {Object} ruleId
     * This param is for rule.
     *
     * @param {Object} updateRuleId
     * The bandwidth limit rule to update.  Required.
     *
     */
    function updateBandwidthRule(policyId, ruleId, updateRuleId) {
      return apiService.patch('/api/neutron/qos/policies/' + policyId +
             '/bandwidth_limit_rules/' + ruleId , updateRuleId)
       .catch(function onError() {
         toastService.add('error', gettext('Unable to update the bandwidthrule.'));
       });
    }

    /**
     * @name updateDSCPMarkingRule
     * @description
     * Update an existing bandwidth limit rule for a QoS policy.
     * @returns {Object} A bandwidth_limit_rule object on success.
     *
     * @param {Object} policyId
     * This param is for qos policy.
     *
     * @param {Object} ruleId
     * This param is for rule.
     *
     * @param {Object} updateRuleId
     * The bandwidth limit rule to update.  Required.
     *
     */
    function updateDSCPMarkingRule(policyId, ruleId, updateRuleId) {
      return apiService.patch('/api/neutron/qos/policies/' + policyId +
             '/dscp_marking_rules/' + ruleId , updateRuleId)
       .catch(function onError() {
         toastService.add('error', gettext('Unable to update the dscp marking rule.'));
       });
    }

    /**
     * @name updateMinimumBandwidthRule
     * @description
     * Update an existing minimum bandwidth rule for a QoS policy.
     * @returns {Object} A minimum_bandwidth_rule object on success.
     *
     * @param {Object} policyId
     * This param is for qos policy.
     *
     * @param {Object} ruleId
     * This param is for rule.
     *
     * @param {Object} updateRuleId
     * The minimum bandwidth limit rule to update. Required.
     *
     */
    function updateMinimumBandwidthRule(policyId, ruleId, updateRuleId) {
      return apiService.patch('/api/neutron/qos/policies/' + policyId +
             '/minimum_bandwidth_rules/' + ruleId , updateRuleId)
       .catch(function onError() {
         toastService.add('error', gettext('Unable to update the minimum bandwidth rule.'));
       });
    }

    /**
     * @name updateMinimumPacketRateRule
     * @description
     * Update an existing minimum packet rate limit rule for a QoS policy.
     * @returns {Object} A minimum_packet_rate_rule object on success.
     *
     * @param {Object} policyId
     * This param is for qos policy.
     *
     * @param {Object} ruleId
     * This param is for rule.
     *
     * @param {Object} updateRuleId
     * The minimum packet rate limit rule to update.  Required.
     *
     */
    function updateMinimumPacketRateRule(policyId, ruleId, updateRuleId) {
      return apiService.patch('/api/neutron/qos/policies/' + policyId +
              '/minimum_packet_rate_rules/' + ruleId , updateRuleId)
        .catch(function onError() {
          toastService.add('error', gettext('Unable to update the minimum packet rate rule.'));
        });
    }

    /**
     * @name deleteBandwidthLimitRule
     * @description
     * Delete a single bandwidth limit rule.
     *
     * @param {string} policyId
     * The ID of the QoS policy.
     *
     * @param {string} deleteruleId
     * The ID of the QoS rule.
     *
     */
    function deleteBandwidthLimitRule(policyId, deleteRuleId) {
      return apiService.delete('/api/neutron/qos/policies/' + policyId +
             '/bandwidth_limit_rules/' + deleteRuleId).catch(function onError() {
               toastService.add('error', gettext('Unable to delete the bandwidth_limit_rule.'));
             });
    }

    /**
     * @name deleteDSCPMarkingRule
     * @description
     * Delete a single dscp mark rule.
     *
     * @param {string} policyId
     * The ID of the QoS policy.
     *
     * @param {string} deleteruleId
     * The ID of the QoS rule.
     */
    function deleteDSCPMarkingRule(policyId, deleteRuleId) {
      return apiService.delete('/api/neutron/qos/policies/' + policyId +
             '/dscp_marking_rules/' + deleteRuleId).catch(function onError() {
               toastService.add('error', gettext('Unable to delete the dscp_marking_rule.'));
             });
    }

    /**
     * @name deleteMinimumBandwidthRule
     * @description
     * Delete a single minimum bandwidth rule.
     *
     * @param {string} policyId
     * The ID of the QoS policy.
     *
     * @param {string} deleteruleId
     * The ID of the QoS rule.
     */
    function deleteMinimumBandwidthRule(policyId, deleteRuleId) {
      return apiService.delete('/api/neutron/qos/policies/' + policyId +
             '/minimum_bandwidth_rules/' + deleteRuleId).catch(function onError() {
               toastService.add('error', gettext('Unable to delete the minimum_bandwidth_rule .'));
             });
    }

    /**
     * @name deleteMinimumPacketRateRule
     * @description
     * Delete a single minimum packet rate rule.
     *
     * @param {string} policyId
     * The ID of the QoS policy.
     *
     * @param {string} deleteruleId
     * The ID of the QoS rule.
     */
    function deleteMinimumPacketRateRule(policyId, deleteRuleId) {
      return apiService.delete('/api/neutron/qos/policies/' + policyId +
            '/minimum_packet_rate_rules/' + deleteRuleId).catch(function onError() {
              toastService.add('error', gettext('Unable to delete the minimum_packet_rate_rule .'));
            });
    }

    // Trunks

    /**
     * @name getTrunk
     * @description
     * Get a single trunk by ID
     *
     * @param {string} id
     * Specifies the id of the trunk to request.
     *
     * @param {boolean} suppressError (optional)
     * Suppress the error toast. Default to showing it.
     *
     * @returns {Object} The result of the API call
     */
    function getTrunk(id, suppressError) {
      var promise = apiService.get('/api/neutron/trunks/' + id + '/')
        .then(function onSuccess(response) {
          convertDatesHumanReadable(response.data);
          return response;
        });
      promise = suppressError ? promise : promise.catch(function onError() {
        var msg = gettext('Unable to retrieve the trunk with id: %(id)s');
        toastService.add('error', interpolate(msg, {id: id}, true));
      });
      return promise;
    }

    /**
     * @name getTrunks
     * @description
     * Get a list of trunks for a tenant.
     *
     * @returns {Object} An object with property "items". Each item is a trunk.
     */
    function getTrunks(params) {
      var config = params ? {'params' : params} : {};
      return apiService.get('/api/neutron/trunks/', config)
        .then(function onSuccess(response) {
          response.data.items.forEach(function(trunk) {
            convertDatesHumanReadable(trunk);
          });
          return response;
        })
        .catch(function onError() {
          toastService.add('error', gettext('Unable to retrieve the trunks.'));
        });
    }

    /**
     * @name createTrunk
     * @description
     * Create a neutron trunk.
     */
    function createTrunk(newTrunk) {
      return apiService.post('/api/neutron/trunks/', newTrunk)
        .catch(function onError() {
          toastService.add('error', gettext('Unable to create the trunk.'));
        });
    }

    /**
     * @name deleteTrunk
     * @description
     * Delete a single neutron trunk.
     *
     * @param {string} trunkId
     * UUID of a trunk to be deleted.
     *
     * @param {boolean} suppressError (optional)
     * Suppress the error toast. Default to showing it.
     */
    function deleteTrunk(trunkId, suppressError) {
      var promise = apiService.delete('/api/neutron/trunks/' + trunkId + '/');
      promise = suppressError ? promise : promise.catch(function onError() {
        var msg = gettext('Unable to delete trunk: %(id)s');
        toastService.add('error', interpolate(msg, { id: trunkId }, true));
      });
      return promise;
    }

    /**
     * @name updateTrunk
     * @description
     * Update an existing trunk.
     */
    function updateTrunk(oldTrunk, newTrunk) {
      return apiService.patch('/api/neutron/trunks/' + oldTrunk.id + '/', [oldTrunk, newTrunk])
      .catch(function onError() {
        toastService.add('error', gettext('Unable to update the trunk.'));
      });
    }

  }
}());
