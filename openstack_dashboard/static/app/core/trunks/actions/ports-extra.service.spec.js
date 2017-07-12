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

  describe('horizon.app.core.trunks.actions.ports-extra.service', function() {

    var service;

    beforeEach(module('horizon.app.core'));
    beforeEach(inject(function($injector) {
      service = $injector.get('horizon.app.core.trunks.actions.ports-extra.service');
    }));

    it('should add network and subnet info', function() {
      var inPorts = [{network_id: 1, fixed_ips: [{subnet_id: 1, ip_address: '1.1.1.1'}]}];
      var networks = [{id : 1, name: 'net1', subnets: [{id: 1, name: 'subnet1'}]}];

      var outPorts = service.addNetworkAndSubnetInfo(inPorts, networks);
      expect(outPorts[0].network_name).toEqual('net1');
      expect(outPorts[0].subnet_names).toEqual({'1.1.1.1': 'subnet1'});
    });

    it('should return the same port object if no network match', function() {
      var inPorts = [{network_id: 1, fixed_ips: [{subnet_id: 1, ip_address: '1.1.1.1'}]}];
      var networks = [{id : 2, name: 'net1'}];

      var outPorts = service.addNetworkAndSubnetInfo(inPorts, networks);
      expect(outPorts[0].network_name).toBeUndefined();
      expect(outPorts[0].subnet_names).toBeUndefined();
    });

    it('should return only network name if no match in subnet', function() {
      var inPorts = [{network_id: 1, fixed_ips: [{subnet_id: 1, ip_address: '1.1.1.1'}]}];
      var networks = [{id : 1, name: 'net1', subnets: [{id: 2, name: 'subnet1'}]}];

      var outPorts = service.addNetworkAndSubnetInfo(inPorts, networks);
      expect(outPorts[0].network_name).toEqual('net1');
      expect(outPorts[0].subnet_names).toEqual({});
    });

    it('should compare port1 and port2 and return -1 if port1 is first', function() {
      var port1 = {name: 'port1', id: '1234'};
      var port2 = {name: 'port2', id: '5678'};
      expect(service.cmpPortsByNameAndId(port1, port2)).toEqual(-1);
    });

    it ('should compare port1 and port2 and return 1 if port2 is first', function() {
      var port1 = {name: 'xxxx1', id: '1234'};
      var port2 = {name: 'port2', id: '5678'};
      expect(service.cmpPortsByNameAndId(port1, port2)).toEqual(1);
    });

    it('should return true if port has trunk_id and it equals with trunkId', function() {
      var trunkId = '1234';
      var port = {trunk_id: '1234'};
      expect(service.isSubportOfTrunk(trunkId, port)).toBe(true);
    });

    it('should return true if port is subport candidate', function() {
      var port = {admin_state_up: true, device_owner: ''};
      expect(service.isSubportCandidate(port)).toBe(true);
    });

    it('should return false if port is not subport candidate', function() {
      var port = {admin_state_up: true, device_owner: '', trunk_id: '1234', trunk_details: {}};
      expect(service.isSubportCandidate(port)).toBe(false);
    });

    it('should return true if port is parent port candidate', function() {
      var port1 = {admin_state_up: true, device_owner: ''};
      var port2 = {admin_state_up: true, device_owner: 'compute:1'};
      expect(service.isParentPortCandidate(port1)).toBe(true);
      expect(service.isParentPortCandidate(port2)).toBe(true);
    });

    it('should return false if port is not parent port candidate', function() {
      var port1 = {admin_state_up: true, device_owner: '', trunk_id: '1234', trunk_details: {}};
      var port2 = {admin_state_up: true, device_owner: 'network:dhcp'};
      expect(service.isParentPortCandidate(port1)).toBe(false);
      expect(service.isParentPortCandidate(port2)).toBe(false);
    });

    it('should compare subports by segmentation type', function() {
      var port1 = {segmentation_type: 'vlan'};
      var port2 = {segmentation_type: 'inherit'};
      expect(service.cmpSubportsBySegmentationTypeAndId(port1, port2)).toBe(1);
    });

    it('should compare subports by segmentation id', function() {
      var port1 = {segmentation_type: 'vlan', segmentation_id: 100};
      var port2 = {segmentation_type: 'vlan', segmentation_id: 1000};
      expect(service.cmpSubportsBySegmentationTypeAndId(port1, port2)).toBeLessThan(0);
    });

  });

})();
