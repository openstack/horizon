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

    beforeEach(module('horizon.framework.util.filters'));
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

  describe("check function", function() {

    var $timeout, service, apiService;

    ////////////////

    beforeEach(module('horizon.framework.conf'));
    beforeEach(module('horizon.framework.util.filters'));
    beforeEach(module('horizon.framework.widgets.toast'));
    beforeEach(module('horizon.app.core.openstack-service-api'));
    beforeEach(module('horizon.framework.util.http'));

    beforeEach(inject(['horizon.app.core.openstack-service-api.policy',
      'horizon.framework.util.http.service', '$timeout',
      function(policyAPI, _apiService, _$timeout_) {
        service = policyAPI;
        apiService = _apiService;
        $timeout = _$timeout_;
      }
    ]));

    ////////////////

    it('should be defined', function defined() {
      expect(service.check).toBeDefined();
    });

    it("returns results from api if no cache", function defined() {
      var input = 'abcdef';
      var successFunc, gotObject;
      var retVal = {
        success: function(x) {
          successFunc = x; return {error: angular.noop};
        }
      };
      var spy = spyOn(apiService, 'post').and.returnValue(retVal);
      service.check(input).then(function(x) { gotObject = x; });
      successFunc({hello: 'there'});
      $timeout.flush();
      expect(gotObject).toEqual({hello: 'there'});
      expect(apiService.post).toHaveBeenCalled();

      spy.calls.reset();
      service.check(input).then(function(x) { gotObject = x; });
      $timeout.flush();
      expect(gotObject).toEqual({hello: 'there'});
      expect(apiService.post).not.toHaveBeenCalled();
    });

  });

  describe("Policy API ifAllowed", function() {

    var $timeout, service, $q;

    ////////////////

    beforeEach(module('horizon.framework.conf'));
    beforeEach(module('horizon.framework.util.filters'));
    beforeEach(module('horizon.framework.widgets.toast'));
    beforeEach(module('horizon.app.core.openstack-service-api'));
    beforeEach(module('horizon.framework.util.http'));

    beforeEach(inject(['horizon.app.core.openstack-service-api.policy',
      '$q', '$timeout',
      function(policyAPI, _$q_, _$timeout_) {
        service = policyAPI;
        $q = _$q_;
        $timeout = _$timeout_;
      }
    ]));

    ////////////////

    it('should be defined', function defined() {
      expect(service.ifAllowed).toBeDefined();
    });

    it("rejects when check() resolves to 'allowed = false'", function() {
      var input = {'expect': 'fail'};
      var def = $q.defer();
      def.resolve({allowed: false});
      var spy = spyOn(service, 'check').and.returnValue(def.promise);
      service.ifAllowed(input).then(failWhenCalled, passWhenCalled);
      $timeout.flush();
      expect(service.check).toHaveBeenCalled();

      //Repeat the call with same inputs and expect same result but to be cached
      spy.calls.reset();
      service.ifAllowed(input).then(failWhenCalled, passWhenCalled);
      $timeout.flush();
      expect(service.check).not.toHaveBeenCalled();
    });

    it("passes when check() resolves to 'allowed = true'", function() {
      var input = {'expect': 'pass'};
      var def = $q.defer();
      def.resolve({allowed: true});
      var spy = spyOn(service, 'check').and.returnValue(def.promise);
      service.ifAllowed(input).then(passWhenCalled, failWhenCalled);
      $timeout.flush();
      expect(service.check).toHaveBeenCalled();

      //Repeat the call with same inputs and expect same result but to be cached
      spy.calls.reset();
      service.ifAllowed(input).then(passWhenCalled, failWhenCalled);
      $timeout.flush();
      expect(service.check).not.toHaveBeenCalled();
    });
  });

  function failWhenCalled() {
    expect(false).toBe(true);
  }
  function passWhenCalled() {
    expect(true).toBe(true);
  }

})();
