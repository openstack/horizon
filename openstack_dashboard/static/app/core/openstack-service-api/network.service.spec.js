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
(function() {
  'use strict';

  describe('Network API', function() {
    var testCall, service;
    var apiService = {};
    var toastService = {};

    beforeEach(function() {
      module('horizon.mock.openstack-service-api', function($provide, initServices) {
        testCall = initServices($provide, apiService, toastService);
      });

      module('horizon.app.core.openstack-service-api');

      inject(['horizon.app.core.openstack-service-api.network', function(networkAPI) {
        service = networkAPI;
      }]);
    });

    it('defines the service', function() {
      expect(service).toBeDefined();
    });

    var tests = [
      {
        func: 'getFloatingIps',
        method: 'get',
        path: '/api/network/floatingips/',
        error: 'Unable to retrieve floating IPs.'
      },
      {
        func: 'getFloatingIpPools',
        method: 'get',
        path: '/api/network/floatingippools/',
        error: 'Unable to retrieve floating IP pools.'
      },
      {
        func: 'allocateFloatingIp',
        method: 'post',
        path: '/api/network/floatingip/',
        data: { pool_id: 'pool' },
        error: 'Unable to allocate new floating IP address.',
        testInput: [ 'pool' ]
      },
      {
        func: 'associateFloatingIp',
        method: 'patch',
        path: '/api/network/floatingip/',
        data: { address_id: 'address', port_id: 'port' },
        error: 'Unable to associate floating IP address.',
        testInput: [ 'address', 'port' ]
      },
      {
        func: 'disassociateFloatingIp',
        method: 'patch',
        path: '/api/network/floatingip/',
        data: { address_id: 'address' },
        error: 'Unable to disassociate floating IP address.',
        testInput: [ 'address' ]
      }
    ];

    // Iterate through the defined tests and apply as Jasmine specs.
    angular.forEach(tests, function(params) {
      it('defines the ' + params.func + ' call properly', function() {
        var callParams = [apiService, service, toastService, params];
        testCall.apply(this, callParams);
      });
    });

  });

})();
