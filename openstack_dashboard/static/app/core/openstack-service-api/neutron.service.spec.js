/*
 *    (c) Copyright 2015 Hewlett-Packard Development Company, L.P.
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

  describe('Neutron API', function() {
    var testCall, service;
    var apiService = {};
    var toastService = {};

    beforeEach(
      module('horizon.mock.openstack-service-api',
        function($provide, initServices) {
          testCall = initServices($provide, apiService, toastService);
        })
    );

    beforeEach(module('horizon.app.core.openstack-service-api'));

    beforeEach(inject(['horizon.app.core.openstack-service-api.neutron', function(neutronAPI) {
      service = neutronAPI;
    }]));

    it('defines the service', function() {
      expect(service).toBeDefined();
    });

    var tests = [

      {
        "func": "getNetworks",
        "method": "get",
        "path": "/api/neutron/networks/",
        "error": "Unable to retrieve the networks."
      },
      {
        "func": "createNetwork",
        "method": "post",
        "path": "/api/neutron/networks/",
        "data": "new net",
        "error": "Unable to create the network.",
        "testInput": [
          "new net"
        ]
      },
      {
        "func": "getSubnets",
        "method": "get",
        "path": "/api/neutron/subnets/",
        "data": 42,
        "error": "Unable to retrieve the subnets.",
        "testInput": [
          42
        ]
      },
      {
        "func": "createSubnet",
        "method": "post",
        "path": "/api/neutron/subnets/",
        "data": "new subnet",
        "error": "Unable to create the subnet.",
        "testInput": [
          "new subnet"
        ]
      },
      {
        "func": "getPorts",
        "method": "get",
        "path": "/api/neutron/ports/",
        "data": 42,
        "error": "Unable to retrieve the ports.",
        "testInput": [
          42
        ]
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
