/*
 * Copyright 2017 Ericsson
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

(function() {
  'use strict';

  angular
    .module('horizon.app.core.trunks')
    .factory('horizon.app.core.trunks.actions.ports-extra.service', portsExtra);

  /**
   * @ngdoc factory
   * @name horizon.app.core.trunks.actions.ports-extra.service
   * @description Ports-related utility functions including:
   *   - filters for various port subtypes
   *   - comparison functions to sort port lists
   *   - etc.
   */
  function portsExtra() {
    var service = {
      addNetworkAndSubnetInfo: addNetworkAndSubnetInfo,
      cmpPortsByNameAndId: cmpPortsByNameAndId,
      cmpSubportsBySegmentationTypeAndId: cmpSubportsBySegmentationTypeAndId,
      isParentPortCandidate: isParentPortCandidate,
      isSubportCandidate: isSubportCandidate,
      isSubportOfTrunk: isSubportOfTrunk
    };

    return service;

    ////////////

    function isParentPortCandidate(port) {
      return (
        port.admin_state_up &&
        // NOTE(bence romsics): A port already booted on may or may not be used
        // as the parent port of a trunk depending on the neutron driver. But
        // we do not (and should not) know anything about neutron driver config
        // so here we cannot filter on device_owner being unset. However the ovs
        // driver is going to throw errors if the user tries to trunk a port
        // already booted.
        (port.device_owner === '' ||
         port.device_owner.indexOf('compute:') === 0) &&
        // port is not a trunk parent already
        !port.trunk_details &&
        // port is not a trunk subport already
        !port.trunk_id
      );
    }

    function isSubportCandidate(port) {
      return (
        port.admin_state_up &&
        // port already booted on must never be a subport
        port.device_owner === '' &&
        // port is not a trunk parent already
        !port.trunk_details &&
        // port is not a trunk subport already
        !port.trunk_id
      );
    }

    function isSubportOfTrunk(trunkId, port) {
      return (
        // port is a trunk subport...
        port.trunk_id &&
        // ...of this trunk
        port.trunk_id === trunkId
      );
    }

    function cmpPortsByNameAndId(a, b) {
      return (
        // primary key: ports with a name sort earlier than ports without
        (a.name === '') - (b.name === '') ||
        // secondary key: name
        a.name.localeCompare(b.name) ||
        // tertiary key: id
        a.id.localeCompare(b.id)
      );
    }

    function cmpSubportsBySegmentationTypeAndId(a, b) {
      return (
        // primary key: segmentation type
        a.segmentation_type.localeCompare(b.segmentation_type) ||
        // secondary key: segmentation id
        (a.segmentation_id - b.segmentation_id)
      );
    }

    function addNetworkAndSubnetInfo(inPorts, networks) {
      var networksDict = {};
      networks.forEach(function(network) {
        networksDict[network.id] = network;
      });
      var outPorts = [];

      inPorts.forEach(function(inPort) {
        var network, outPort;
        outPort = angular.copy(inPort);
        // NOTE(bence romsics): Ports and networks may not be in sync,
        // therefore some ports may not get their network and subnet
        // info. But we return (and so display) all ports anyway.
        if (inPort.network_id in networksDict) {
          network = networksDict[inPort.network_id];
          outPort.network_name = network.name;
          outPort.subnet_names = getSubnetsForPort(inPort, network.subnets);
        }
        outPorts.push(outPort);
      });

      return outPorts;
    }

    function getSubnetsForPort(port, subnets) {
      var subnetNames = {};
      port.fixed_ips.forEach(function(ip) {
        subnets.forEach(function(subnet) {
          if (ip.subnet_id === subnet.id) {
            subnetNames[ip.ip_address] = subnet.name;
          }
        });
      });
      return subnetNames;
    }

  }
})();
