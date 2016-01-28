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

  describe("serviceCatalog", function() {
    var factory, q, keystoneAPI, userSession, deferred;

    beforeEach(module('horizon.app.core.openstack-service-api'));

    beforeEach(module(function($provide) {
      keystoneAPI = {serviceCatalog: angular.noop};
      $provide.value('horizon.app.core.openstack-service-api.keystone', keystoneAPI);
      userSession = {get: angular.noop};
      $provide.value('horizon.app.core.openstack-service-api.userSession', userSession);
      deferred = {promise: angular.noop, reject: angular.noop, resolve: angular.noop};
      q = {all: function() {return {then: angular.noop}; },
           defer: function() { return deferred; }};
      $provide.value('$q', q);
      $provide.value('$cacheFactory', function() { return 'cache'; });
    }));

    beforeEach(
      inject(['horizon.app.core.openstack-service-api.serviceCatalog', function(serviceCatalog) {
        factory = serviceCatalog;
      }])
    );

    it('defines the factory', function() {
      expect(factory).toBeDefined();
    });

    it('defines .cache', function() {
      expect(factory.cache).toBe("cache");
    });

    it('defines .get', function() {
      expect(factory.get).toBeDefined();
    });

    describe(".get() features", function() {
      var postAction = {then: angular.noop};

      beforeEach(function() {
        spyOn(keystoneAPI, 'serviceCatalog').and.returnValue(postAction);
        spyOn(postAction, 'then');
        factory.get();
      });

      it("gets the service catalog", function() {
        expect(keystoneAPI.serviceCatalog).toHaveBeenCalled();
      });

      it("then returns the response's data member", function() {
        var func = postAction.then.calls.argsFor(0)[0];
        expect(func({data: 'thing'})).toBe("thing");
      });

    });

    it('defines .ifTypeEnabled', function() {
      expect(factory.ifTypeEnabled).toBeDefined();
    });

    describe(".ifTypeEnabled features", function() {
      var postAction = {then: angular.noop};

      beforeEach(function() {
        spyOn(q, 'all').and.returnValue(postAction);
        spyOn(factory, 'get');
        spyOn(postAction, 'then');
        spyOn(deferred, 'reject');
        spyOn(deferred, 'resolve');
      });

      var callMethod = function(type, data, resolved) {
        factory.ifTypeEnabled(type);
        expect(q.all).toHaveBeenCalled();

        var successFunc = postAction.then.calls.argsFor(0)[0];
        var failFunc = postAction.then.calls.argsFor(0)[1];
        successFunc(data);

        // If we expected this to be resolved, then expect
        // both that we did call resolve() and did NOT call reject().
        // Vice versa if expecting rejection.
        if (resolved) {
          expect(deferred.resolve).toHaveBeenCalled();
          expect(deferred.reject).not.toHaveBeenCalled();
        } else {
          expect(deferred.resolve).not.toHaveBeenCalled();
          expect(deferred.reject).toHaveBeenCalled();
        }

        deferred.reject.calls.reset();
        failFunc();
        expect(deferred.reject).toHaveBeenCalled();
      };

      it("accepts 'desired' type with no matches; is rejected", function() {
        var data = {catalog: [1, 2, 3],
                    session: {services_region: true}};
        callMethod("desired", data, false);
      });

      it("accepts 'desired' type with matches but no endpoints; is rejected", function() {
        var data = {catalog: [1, {type: "desired", endpoints: []}, 3],
                    session: {services_region: true}};
        callMethod("desired", data, false);
      });

      it("accepts 'desired' type with a match; is resolved", function() {
        var data = {catalog: [{type: "desired", endpoints: [{region_id: true}]}],
                    session: {services_region: true}};
        callMethod("desired", data, true);
      });

      it("accepts 'desired' type with matches and region is true; is resolved", function() {
        var data = {catalog: [{type: "desired", endpoints: [{region: true}]}],
                    session: {services_region: true}};
        callMethod("desired", data, true);
      });

      it("accepts 'desired' type with matches and service_region is true; is resolved", function() {
        var data = {catalog: [{type: "identity"}],
                    session: {services_region: true}};
        callMethod("identity", data, true);
      });
    });

  });
})();
