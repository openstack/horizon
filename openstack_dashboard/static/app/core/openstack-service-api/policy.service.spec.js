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

  describe("check function", function() {

    var $timeout, service, apiService;

    ////////////////

    beforeEach(module('horizon.framework.conf'));
    beforeEach(module('horizon.framework.widgets.toast'));
    beforeEach(module('horizon.app.core.openstack-service-api'));
    beforeEach(module('horizon.framework.util.http'));

    beforeEach(inject(['horizon.app.core.openstack-service-api.policy',
      'horizon.framework.util.http.service', '$timeout',
      function(policyAPI, _apiService, _$timeout_) {
        service = policyAPI;
        apiService = _apiService;
        $timeout = _$timeout_;
        service.cache.removeAll();
      }
    ]));

    ////////////////

    it('should be defined', function defined() {
      expect(service.check).toBeDefined();
    });

    it("should use the cache if it's populated", function defined() {
      service.cache.put(angular.toJson('abcdef'), {mission: 'impossible'});
      var data;

      function verifyData(x) {
        data = x;
      }
      service.check('abcdef').then(verifyData);
      $timeout.flush();
      expect(data).toEqual({mission: 'impossible'});
    });

    it("returns results from api if no cache", function defined() {
      var successFunc, gotObject;
      var retVal = {
        success: function(x) {
          successFunc = x; return {error: angular.noop};
        }
      };
      spyOn(apiService, 'post').and.returnValue(retVal);
      service.check('abcdef').then(function(x) { gotObject = x; });
      successFunc({hello: 'there'});
      $timeout.flush();
      expect(gotObject).toEqual({hello: 'there'});
    });

    it("sets cache with results from apiService if no cache already", function defined() {
      var successFunc;
      var retVal = {
        success: function(x) {
          successFunc = x;
          return { error: angular.noop };
        }
      };
      spyOn(apiService, 'post').and.returnValue(retVal);
      service.check('abcdef').then(angular.noop);
      successFunc({hello: 'there'});
      $timeout.flush();
      expect(service.cache.get(angular.toJson('abcdef'))).toEqual({hello: 'there'});
    });

  });

  describe("Policy API ifAllowed", function() {

    var $timeout, service, $q;

    ////////////////

    beforeEach(module('horizon.framework.conf'));
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

    it("rejects when check() resolves with an object without 'allowed'", function() {
      var def = $q.defer();
      def.resolve({allowed: false});
      spyOn(service, 'check').and.returnValue(def.promise);
      service.ifAllowed({}).then(failWhenCalled, passWhenCalled);
      $timeout.flush();
    });

    it("passes when check() resolves with an object with 'allowed'", function() {
      var def = $q.defer();
      def.resolve({allowed: true});
      spyOn(service, 'check').and.returnValue(def.promise);
      service.ifAllowed({}).then(passWhenCalled, failWhenCalled);
      $timeout.flush();
    });
  });

  function failWhenCalled() {
    expect(false).toBe(true);
  }
  function passWhenCalled() {
    expect(true).toBe(true);
  }

})();
