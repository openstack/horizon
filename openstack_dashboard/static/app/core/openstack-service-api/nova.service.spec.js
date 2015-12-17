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
        "func": "getServices",
        "method": "get",
        "path": "/api/nova/services/",
        "error": "Unable to retrieve the nova services."
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
        "func": "getAvailabilityZones",
        "method": "get",
        "path": "/api/nova/availzones/",
        "error": "Unable to retrieve the availability zones."
      },
      {
        "func": "getLimits",
        "method": "get",
        "path": "/api/nova/limits/",
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
          false,
          false
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
          true,
          false
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
          false,
          true
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
          true,
          true
        ]
      },
      {
        "func": "getFlavor",
        "method": "get",
        "path": "/api/nova/flavors/42",
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
        "path": "/api/nova/flavors/42",
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
