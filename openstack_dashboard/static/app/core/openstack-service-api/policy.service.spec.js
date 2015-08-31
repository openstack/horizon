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

  describe('Policy API check', function() {
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

    beforeEach(inject(['horizon.app.core.openstack-service-api.policy', function(policyAPI) {
      service = policyAPI;
    }]));

    it('defines the service', function() {
      expect(service).toBeDefined();
    });

    var tests = [
      {
        "func": "check",
        "method": "post",
        "path": "/api/policy/",
        "data": "rules",
        "error": "Policy check failed.",
        "testInput": [
          "rules"
        ],
        "messageType": "warning"
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

  describe("Policy API ifAllowed", function() {

    var policy = { rules:[] };
    var response = {
      data: { allowed: true }
    };

    var deferred = {
      then: function(callback) { callback(response); },
      reject: angular.noop,
      resolve: angular.noop
    };

    var service;
    var q = { defer: function() { return deferred; }};

    ////////////////

    beforeEach(module('horizon.framework.conf'));
    beforeEach(module('horizon.framework.util.http'));
    beforeEach(module('horizon.framework.widgets.toast'));
    beforeEach(module('horizon.app.core.openstack-service-api'));
    beforeEach(module(function($provide) {
      $provide.value('$q', q);
    }));

    beforeEach(inject(['horizon.app.core.openstack-service-api.policy', function(policyAPI) {
      service = policyAPI;
    }]));

    beforeEach(function() {
      spyOn(service, 'check').and.returnValue(deferred);
      spyOn(deferred, 'resolve');
      spyOn(deferred, 'reject');
    });

    ////////////////

    it('should be defined', defined);
    it("rejects if response allowed is false", rejects);
    it("resolves if response allowed is true", resolves);

    ////////////////

    function defined() {
      expect(service.ifAllowed).toBeDefined();
    }

    function rejects() {
      response.data.allowed = false;
      service.ifAllowed(policy);
      expect(service.check).toHaveBeenCalledWith(policy);
      expect(deferred.reject).toHaveBeenCalled();
    }

    function resolves() {
      response.data.allowed = true;
      service.ifAllowed(policy);
      expect(service.check).toHaveBeenCalledWith(policy);
      expect(deferred.resolve).toHaveBeenCalled();
    }

  });

})();
