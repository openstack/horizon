/**
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

    beforeEach(function() {
      module('horizon.mock.openstack-service-api', function($provide, initServices) {
        testCall = initServices($provide, apiService, toastService);
      });

      module('horizon.app.core.openstack-service-api');

      inject(['horizon.app.core.openstack-service-api.neutron', function(neutronAPI) {
        service = neutronAPI;
      }]);
    });

    it('defines the service', function() {
      expect(service).toBeDefined();
    });

    it('converts created_at and updated_at to human readable if calling getTrunk' +
       'or getQosPolicy',function() {
      var data = {
        id: 1,
        created_at: '2017-11-16',
        updated_at: '2017-11-16'
      };
      spyOn(apiService, 'get').and.callFake(function() {
        return {
          success: function(c) {
            c(data);
            return this;
          },
          error: function(c) {
            c();
            return this;
          }
        };
      });
      service.getTrunk(data.id, true).success(function(result) {
        expect(result.id).toEqual(data.id);
        expect(result.created_at).toEqual(new Date(data.created_at));
        expect(result.updated_at).toEqual(new Date(data.updated_at));
      });
      service.getQosPolicy(data.id, true).success(function(result) {
        expect(result.id).toEqual(data.id);
        expect(result.created_at).toEqual(new Date(data.created_at));
        expect(result.updated_at).toEqual(new Date(data.updated_at));
      });
    });

    it('converts created_at and updated_at to human readable if calling getTrunks' +
       'or getQoSPolicies', function() {
      var data = {items: [{
        id: 1,
        created_at: '2017-11-16',
        updated_at: '2017-11-16'
      }]};
      spyOn(apiService, 'get').and.callFake(function() {
        return {
          success: function(c) {
            c(data);
            return this;
          },
          error: function(c) {
            c();
            return this;
          }
        };
      });
      service.getTrunks().success(function(result) {
        result.items.forEach(function(trunk) {
          expect(trunk.id).toEqual(data.items[0].id);
          expect(trunk.created_at).toEqual(new Date(data.items[0].created_at));
          expect(trunk.updated_at).toEqual(new Date(data.items[0].updated_at));
        });
      });
      service.getQoSPolicies().success(function(result) {
        result.items.forEach(function(policy) {
          expect(policy.id).toEqual(data.items[0].id);
          expect(policy.created_at).toEqual(new Date(data.items[0].created_at));
          expect(policy.updated_at).toEqual(new Date(data.items[0].updated_at));
        });
      });
    });

    it('can suppress errors in case of deleting trunks', function() {
      spyOn(apiService, 'delete').and.callFake(function() {
        return {
          success: function(c) {
            c();
            return this;
          },
          error: function(c) {
            c();
            return this;
          }
        };
      });
      spyOn(toastService, 'add').and.callThrough();

      service.deleteTrunk('42', true).error(function() {
        expect(toastService.add).not.toHaveBeenCalled();
      });
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
        "data": {
          params: {
            network_id: 42
          }
        },
        "error": "Unable to retrieve the ports.",
        "testInput": [
          {
            network_id: 42
          }
        ]
      },
      {
        "func": "getPorts",
        "method": "get",
        "path": "/api/neutron/ports/",
        "data": {},
        "error": "Unable to retrieve the ports."
      },
      {
        "func": "getAgents",
        "method": "get",
        "path": "/api/neutron/agents/",
        "error": "Unable to retrieve the agents."
      },
      {
        "func": "getExtensions",
        "method": "get",
        "path": "/api/neutron/extensions/",
        "error": "Unable to retrieve the extensions."
      },
      {
        "func": "getDefaultQuotaSets",
        "method": "get",
        "path": "/api/neutron/quota-sets/defaults/",
        "error": "Unable to retrieve the default quotas."
      },
      {
        "func": "updateProjectQuota",
        "method": "patch",
        "path": "/api/neutron/quotas-sets/42",
        "data": {
          "network": 42
        },
        "error": "Unable to update project quota data.",
        "testInput": [
          {
            "network": 42
          },
          42
        ]
      },
      {
        "func": "getTrunk",
        "method": "get",
        "path": "/api/neutron/trunks/42/",
        "error": "Unable to retrieve the trunk with id: 42",
        "testInput": [
          42
        ]
      },
      {
        "func": "getTrunks",
        "method": "get",
        "path": "/api/neutron/trunks/",
        "data": {},
        "error": "Unable to retrieve the trunks."
      },
      {
        "func": "getTrunks",
        "method": "get",
        "path": "/api/neutron/trunks/",
        "data": {
          "params": {
            "project_id": 1
          }
        },
        "testInput": [
          {"project_id": 1}
        ],
        "error": "Unable to retrieve the trunks."
      },
      {
        "func": "createTrunk",
        "method": "post",
        "path": "/api/neutron/trunks/",
        "data": "new trunk",
        "error": "Unable to create the trunk.",
        "testInput": [
          "new trunk"
        ]
      },
      {
        "func": "deleteTrunk",
        "method": "delete",
        "path": "/api/neutron/trunks/42/",
        "error": "Unable to delete trunk: 42",
        "testInput": [
          42
        ]
      },
      {
        "func": "updateTrunk",
        "method": "patch",
        "path": "/api/neutron/trunks/42/",
        "error": "Unable to update the trunk.",
        "data": [
          {"id": 42, "name": "trunk1"},
          {"name": "trunk2"}
        ],
        "testInput": [
          {"id": 42, "name": "trunk1"},
          {"name": "trunk2"}
        ]
      },
      {
        "func": "getQosPolicy",
        "method": "get",
        "path": "/api/neutron/qos_policies/1/",
        "error": "Unable to retrieve the policy with ID 1",
        "testInput": [
          1
        ]
      },
      {
        "func": "getQoSPolicies",
        "method": "get",
        "path": "/api/neutron/qos_policies/",
        "data": {},
        "error": "Unable to retrieve the qos policies."
      },
      {
        "func": "getQoSPolicies",
        "method": "get",
        "path": "/api/neutron/qos_policies/",
        "data": {
          "params": {
            "project_id": 1
          }
        },
        "testInput": [
          {"project_id": 1}
        ],
        "error": "Unable to retrieve the qos policies."
      },
      {
        "func": "deletePolicy",
        "method": "delete",
        "path": "/api/neutron/qos_policies/63/",
        "error": "Unable to delete qos policy 63",
        "testInput": [
          63
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
