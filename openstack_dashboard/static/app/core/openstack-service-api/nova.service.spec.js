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

  describe('Nova API', function() {
    var service;
    var apiService = {};
    var toastService = {};

    beforeEach(module('horizon.app.core.openstack-service-api'));

    beforeEach(module(function($provide) {
      window.apiTest.initServices($provide, apiService, toastService);
    }));

    beforeEach(inject(['horizon.app.core.openstack-service-api.nova', function(novaAPI) {
      service = novaAPI;
    }]));

    it('defines the service', function() {
      expect(service).toBeDefined();
    });

    var tests = [
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
        "path": "/api/nova/flavors/42/extra-specs",
        "error": "Unable to retrieve the flavor extra specs.",
        "testInput": [
          42
        ]
      }

    ];

    // Iterate through the defined tests and apply as Jasmine specs.
    angular.forEach(tests, function(params) {
      it('defines the ' + params.func + ' call properly', function() {
        var callParams = [apiService, service, toastService, params];
        window.apiTest.testCall.apply(this, callParams);
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

  describe("novaExtensions", function() {
    var factory, q, novaAPI;

    beforeEach(module('horizon.app.core.openstack-service-api'));

    beforeEach(module(function($provide) {
      novaAPI = {getExtensions: function() {return {then: angular.noop};}};
      q = {defer: function() { return {resolve: angular.noop}; }};
      $provide.value('$cacheFactory', function() {return "cache";});
      $provide.value('$q', q);
      $provide.value('horizon.app.core.openstack-service-api.nova', novaAPI);
    }));

    beforeEach(inject(function($injector) {
      factory = $injector.get('horizon.app.core.openstack-service-api.novaExtensions');
    }));

    it("is defined", function() {
      expect(factory).toBeDefined();
    });

    it("defines .cache", function() {
      expect(factory.cache).toBeDefined();
    });

    it("defines .get", function() {
      expect(factory.get).toBeDefined();
      var postAction = {then: angular.noop};
      spyOn(novaAPI, 'getExtensions').and.returnValue(postAction);
      spyOn(postAction, 'then');
      factory.get();
      expect(novaAPI.getExtensions).toHaveBeenCalledWith({cache: factory.cache});
      expect(postAction.then).toHaveBeenCalled();
      var func = postAction.then.calls.argsFor(0)[0];
      var testData = {data: {items: [1, 2, 3]}};
      expect(func(testData)).toEqual([1, 2, 3]);
    });

    it("defines .ifNameEnabled", function() {
      expect(factory.ifNameEnabled).toBeDefined();
      var postAction = {then: angular.noop};
      var deferred = {reject: angular.noop, resolve: angular.noop};
      spyOn(q, 'defer').and.returnValue(deferred);
      spyOn(factory, 'get').and.returnValue(postAction);
      spyOn(postAction, 'then');
      factory.ifNameEnabled("desired");
      expect(factory.get).toHaveBeenCalled();
      var func1 = postAction.then.calls.argsFor(0)[0];
      var func2 = postAction.then.calls.argsFor(0)[1];
      spyOn(deferred, 'reject');
      func1();
      expect(deferred.reject).toHaveBeenCalled();

      spyOn(deferred, 'resolve');
      var extensions = [{name: "desired"}];
      func1(extensions);
      expect(deferred.resolve).toHaveBeenCalled();

      deferred.reject.calls.reset();
      func2();
      expect(deferred.reject).toHaveBeenCalledWith('Cannot get the Nova extension list.');
    });

    it("defines .ifEnabled", function() {
      expect(factory.ifEnabled).toBeDefined();
    });
  });
})();
