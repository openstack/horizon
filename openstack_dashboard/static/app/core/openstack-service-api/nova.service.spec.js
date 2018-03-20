/*
 * (c) Copyright 2015 Hewlett-Packard Development Company, L.P.
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

  describe('Nova API', function() {
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

    beforeEach(inject(['horizon.app.core.openstack-service-api.nova', function(novaAPI) {
      service = novaAPI;
    }]));

    it('defines the service', function() {
      expect(service).toBeDefined();
    });

    var tests = [
      {
        "func": "isFeatureSupported",
        "method": "get",
        "path": "/api/nova/features/fake",
        "error": "Unable to check the Nova service feature.",
        "testInput": [
          "fake"
        ]
      },
      {
        "func": "getServices",
        "method": "get",
        "path": "/api/nova/services/",
        "error": "Unable to retrieve the nova services."
      },
      {
        "func": "getConsoleLog",
        "method": "post",
        "path": "/api/nova/servers/123/console-output/",
        "data": {
          "length": 6
        },
        "error": "Unable to load the server console log.",
        "testInput": [123, 6]
      },
      {
        "func": "getActionList",
        "method": "get",
        "path": "/api/nova/servers/123/actions/",
        "error": "Unable to load the server actions.",
        "testInput": [123]
      },
      {
        "func": "getConsoleLog",
        "method": "post",
        "path": "/api/nova/servers/123/console-output/",
        "data": {},
        "error": "Unable to load the server console log.",
        "testInput": [123]
      },
      {
        "func": "getConsoleInfo",
        "method": "post",
        "path": "/api/nova/servers/123/console-info/",
        "data": {
          "console_type": "VNC"
        },
        "error": "Unable to load the server console info.",
        "testInput": [123, "VNC"]
      },
      {
        "func": "getConsoleInfo",
        "method": "post",
        "path": "/api/nova/servers/123/console-info/",
        "data": {},
        "error": "Unable to load the server console info.",
        "testInput": [123]
      },
      {
        "func": "getServerVolumes",
        "method": "get",
        "path": "/api/nova/servers/123/volumes/",
        "error": "Unable to load the server volumes.",
        "testInput": [123]
      },
      {
        "func": "getServerSecurityGroups",
        "method": "get",
        "path": "/api/nova/servers/123/security-groups/",
        "error": "Unable to load the server security groups.",
        "testInput": [123]
      },
      {
        "func": "getKeypairs",
        "method": "get",
        "path": "/api/nova/keypairs/",
        "error": "Unable to retrieve the keypairs."
      },
      {
        "func": "createKeypair",
        "method": "post",
        "path": "/api/nova/keypairs/",
        "data": {
          "public_key": true
        },
        "error": "Unable to import the keypair.",
        "testInput": [
          {
            "public_key": true
          }
        ]
      },
      {
        "func": "createKeypair",
        "method": "post",
        "path": "/api/nova/keypairs/",
        "data": {},
        "error": "Unable to create the keypair.",
        "testInput": [
          {}
        ]
      },
      {
        "func": "deleteKeypair",
        "method": "delete",
        "path": "/api/nova/keypairs/19",
        "error": "Unable to delete the keypair with name: 19",
        "testInput": [19]
      },
      {
        "func": "deleteKeypair",
        "method": "delete",
        "path": "/api/nova/keypairs/19",
        "testInput": [19, true]
      },
      {
        "func": "getKeypair",
        "method": "get",
        "path": "/api/nova/keypairs/19",
        "error": "Unable to retrieve the keypair.",
        "testInput": [19]
      },
      {
        "func": "deleteServer",
        "method": "delete",
        "path": "/api/nova/servers/12",
        "error": "Unable to delete the server with id: 12",
        "testInput": [12]
      },
      {
        "func": "deleteServer",
        "method": "delete",
        "path": "/api/nova/servers/12",
        "testInput": [12, true]
      },
      {
        "func": "createServerSnapshot",
        "method": "post",
        "path": "/api/nova/snapshots/",
        "data": {info: 12},
        "error": "Unable to create the server snapshot.",
        "testInput": [{info: 12}]
      },
      {
        "func": "startServer",
        "method": "post",
        "path": "/api/nova/servers/12",
        "data": { operation: 'start' },
        "error": "Unable to start the server with id: 12",
        "testInput": [12]
      },
      {
        "func": "stopServer",
        "method": "post",
        "path": "/api/nova/servers/12",
        "data": { operation: 'stop' },
        "error": "Unable to stop the server with id: 12",
        "testInput": [12]
      },
      {
        "func": "stopServer",
        "method": "post",
        "path": "/api/nova/servers/12",
        "data": { operation: 'stop' },
        "testInput": [12, true]
      },
      {
        "func": "pauseServer",
        "method": "post",
        "path": "/api/nova/servers/12",
        "data": { operation: 'pause' },
        "error": "Unable to pause the server with id: 12",
        "testInput": [12]
      },
      {
        "func": "unpauseServer",
        "method": "post",
        "path": "/api/nova/servers/12",
        "data": { operation: 'unpause' },
        "error": "Unable to unpause the server with id: 12",
        "testInput": [12]
      },
      {
        "func": "suspendServer",
        "method": "post",
        "path": "/api/nova/servers/12",
        "data": { operation: 'suspend' },
        "error": "Unable to suspend the server with id: 12",
        "testInput": [12]
      },
      {
        "func": "resumeServer",
        "method": "post",
        "path": "/api/nova/servers/12",
        "data": { operation: 'resume' },
        "error": "Unable to resume the server with id: 12",
        "testInput": [12]
      },
      {
        "func": "softRebootServer",
        "method": "post",
        "path": "/api/nova/servers/12",
        "data": { operation: 'soft_reboot' },
        "error": "Unable to soft-reboot the server with id: 12",
        "testInput": [12]
      },
      {
        "func": "hardRebootServer",
        "method": "post",
        "path": "/api/nova/servers/12",
        "data": { operation: 'hard_reboot' },
        "error": "Unable to hard-reboot the server with id: 12",
        "testInput": [12]
      },
      {
        "func": "getAvailabilityZones",
        "method": "get",
        "path": "/api/nova/availzones/",
        "error": "Unable to retrieve the availability zones."
      },
      {
        "func": "getLimits",
        "method": "get",
        "path": "/api/nova/limits/",
        "data": {
          "params": {
            "reserved": undefined
          }
        },
        "error": "Unable to retrieve the limits."
      },
      {
        "func": "createServer",
        "method": "post",
        "path": "/api/nova/servers/",
        "data": "new server",
        "error": "Unable to create the server.",
        "testInput": [
          "new server"
        ]
      },
      {
        "func": "getServer",
        "method": "get",
        "path": "/api/nova/servers/42",
        "error": "Unable to retrieve the server.",
        "testInput": [
          42
        ]
      },
      {
        "func": "getServers",
        "method": "get",
        "path": "/api/nova/servers/",
        "error": "Unable to retrieve instances."
      },
      {
        "func": "getServerGroup",
        "method": "get",
        "path": "/api/nova/servergroups/17",
        "error": "Unable to retrieve the server group.",
        "testInput": [
          '17'
        ]
      },
      {
        "func": 'getServerGroups',
        "method": 'get',
        "path": '/api/nova/servergroups/',
        "error": 'Unable to retrieve server groups.'
      },
      {
        "func": "createServerGroup",
        "method": "post",
        "path": "/api/nova/servergroups/",
        "data": "new server group",
        "error": "Unable to create the server group.",
        "testInput": [
          "new server group"
        ]
      },
      {
        "func": "deleteServerGroup",
        "method": "delete",
        "path": "/api/nova/servergroups/1/",
        "error": "Unable to delete the server group with id 1",
        "testInput": [1]
      },
      {
        "func": "getExtensions",
        "method": "get",
        "path": "/api/nova/extensions/",
        "data": "config",
        "error": "Unable to retrieve the extensions.",
        "testInput": [
          "config"
        ]
      },
      {
        "func": "getFlavors",
        "method": "get",
        "path": "/api/nova/flavors/",
        "data": {
          "params": {}
        },
        "error": "Unable to retrieve the flavors.",
        "testInput": [
        ]
      },
      {
        "func": "getFlavors",
        "method": "get",
        "path": "/api/nova/flavors/",
        "data": {
          "params": {
            "is_public": "true"
          }
        },
        "error": "Unable to retrieve the flavors.",
        "testInput": [
          {is_public: "true"}
        ]
      },
      {
        "func": "getFlavors",
        "method": "get",
        "path": "/api/nova/flavors/",
        "data": {
          "params": {
            "get_extras": "true"
          }
        },
        "error": "Unable to retrieve the flavors.",
        "testInput": [
          {get_extras: "true"}
        ]
      },
      {
        "func": "getFlavors",
        "method": "get",
        "path": "/api/nova/flavors/",
        "data": {
          "params": {
            "is_public": "true",
            "get_extras": "true"
          }
        },
        "error": "Unable to retrieve the flavors.",
        "testInput": [
          {is_public: "true", get_extras: "true"}
        ]
      },
      {
        "func": "getFlavor",
        "method": "get",
        "path": "/api/nova/flavors/42/",
        "data": {
          "params": {
            "get_extras": "true"
          }
        },
        "error": "Unable to retrieve the flavor.",
        "testInput": [
          42,
          true
        ]
      },
      {
        "func": "getFlavor",
        "method": "get",
        "path": "/api/nova/flavors/42/",
        "data": {
          "params": {
            "get_extras": "true",
            "get_access_list": "true"
          }
        },
        "error": "Unable to retrieve the flavor.",
        "testInput": [
          42,
          true,
          true
        ]
      },
      {
        "func": "getFlavor",
        "method": "get",
        "path": "/api/nova/flavors/42/",
        "data": {
          "params": {}
        },
        "error": "Unable to retrieve the flavor.",
        "testInput": [
          42,
          false
        ]
      },
      {
        "func": "getFlavorExtraSpecs",
        "method": "get",
        "path": "/api/nova/flavors/42/extra-specs/",
        "error": "Unable to retrieve the flavor extra specs.",
        "testInput": [
          42
        ]
      },
      {
        "func": "editFlavorExtraSpecs",
        "method": "patch",
        "path": "/api/nova/flavors/42/extra-specs/",
        "data": {
          "updated": {a: '1', b: '2'},
          "removed": ['c', 'd']
        },
        "error": "Unable to edit the flavor extra specs.",
        "testInput": [
          42, {a: '1', b: '2'}, ['c', 'd']
        ]
      },
      {
        "func": "getAggregateExtraSpecs",
        "method": "get",
        "path": "/api/nova/aggregates/42/extra-specs/",
        "error": "Unable to retrieve the aggregate extra specs.",
        "testInput": [
          42
        ]
      },
      {
        "func": "editAggregateExtraSpecs",
        "method": "patch",
        "path": "/api/nova/aggregates/42/extra-specs/",
        "data": {
          "updated": {a: '1', b: '2'},
          "removed": ['c', 'd']
        },
        "error": "Unable to edit the aggregate extra specs.",
        "testInput": [
          42, {a: '1', b: '2'}, ['c', 'd']
        ]
      },
      {
        "func": "getInstanceMetadata",
        "method": "get",
        "path": "/api/nova/servers/42/metadata",
        "error": "Unable to retrieve instance metadata.",
        "testInput": [
          42
        ]
      },
      {
        "func": "editInstanceMetadata",
        "method": "patch",
        "path": "/api/nova/servers/42/metadata",
        "data": {
          "updated": {a: '1', b: '2'},
          "removed": ['c', 'd']
        },
        "error": "Unable to edit instance metadata.",
        "testInput": [
          42, {a: '1', b: '2'}, ['c', 'd']
        ]
      },
      {
        "func": "createFlavor",
        "method": "post",
        "path": "/api/nova/flavors/",
        "data": 42,
        "error": "Unable to create the flavor.",
        "testInput": [
          42
        ]
      },
      {
        "func": "updateFlavor",
        "method": "patch",
        "path": "/api/nova/flavors/42/",
        "data": {
          id: 42
        },
        "error": "Unable to update the flavor.",
        "testInput": [
          {
            id: 42
          }
        ]
      },
      {
        "func": "deleteFlavor",
        "method": "delete",
        "path": "/api/nova/flavors/42/",
        "error": "Unable to delete the flavor with id: 42",
        "testInput": [42]
      },
      {
        "func": "deleteFlavor",
        "method": "delete",
        "path": "/api/nova/flavors/42/",
        "testInput": [42, true]
      },
      {
        "func": "getDefaultQuotaSets",
        "method": "get",
        "path": "/api/nova/quota-sets/defaults/",
        "error": "Unable to retrieve the default quotas."
      },
      {
        "func": "setDefaultQuotaSets",
        "method": "patch",
        "data": {
          "id": 42
        },
        "testInput": [
          {
            "id": 42
          }
        ],
        "path": "/api/nova/quota-sets/defaults/",
        "error": "Unable to set the default quotas."
      },
      {
        "func": "getEditableQuotas",
        "method": "get",
        "path": "/api/nova/quota-sets/editable/",
        "error": "Unable to retrieve the editable quotas."
      },
      {
        "func": "updateProjectQuota",
        "method": "patch",
        "path": "/api/nova/quota-sets/42",
        "data": {
          "cores": 42
        },
        "error": "Unable to update project quota data.",
        "testInput": [
          {
            "cores": 42
          },
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

    it('getFlavors converts specific property names with : in them', function() {
      var postAction = {success: angular.noop};
      spyOn(apiService, 'get').and.returnValue(postAction);
      spyOn(postAction, 'success').and.returnValue({error: angular.noop});
      service.getFlavors();
      var func = postAction.success.calls.argsFor(0)[0];

      // won't do anything.  Need to test that it won't do anything.
      func();

      var data = {items: [{nada: 'puesNada'}]};
      func(data);
      expect(data).toEqual({items: [{nada: 'puesNada'}]});

      data = {items: [{'OS-FLV-EXT-DATA:ephemeral': true}]};
      func(data);
      expect(data).toEqual({items: [{'OS-FLV-EXT-DATA:ephemeral': true, ephemeral: true}]});

      data = {items: [{'OS-FLV-DISABLED:disabled': true}]};
      func(data);
      expect(data).toEqual({items: [{'OS-FLV-DISABLED:disabled': true, disabled: true}]});

      data = {items: [{'os-flavor-access:is_public': true}]};
      func(data);
      expect(data).toEqual({items: [{'os-flavor-access:is_public': true, is_public: true}]});

    });

  });

})();
