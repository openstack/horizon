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
(function () {
  'use strict';

  describe("userSession", function() {
    var factory, keystoneAPI, $q, $timeout;

    beforeEach(module('horizon.app.core.openstack-service-api'));

    beforeEach(module(function($provide) {
      keystoneAPI = {getCurrentUserSession: angular.noop};
      $provide.value('horizon.app.core.openstack-service-api.keystone', keystoneAPI);
      $provide.value('$cacheFactory', function() { return 'cache'; });
    }));

    beforeEach(inject(['horizon.app.core.openstack-service-api.userSession', function(userSession) {
      factory = userSession;
    }]));

    beforeEach(inject(function(_$q_, _$timeout_) {
      $q = _$q_;
      $timeout = _$timeout_;
    }));

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
        spyOn(keystoneAPI, 'getCurrentUserSession').and.returnValue(postAction);
        spyOn(postAction, 'then');
        factory.get();
      });

      it("calls getCurrentUserSession", function() {
        expect(keystoneAPI.getCurrentUserSession).toHaveBeenCalled();
      });

      it("then returns the response's data member", function() {
        var func = postAction.then.calls.argsFor(0)[0];
        expect(func({data: 'thing'})).toBe("thing");
      });
    });

    describe('isCurrentProject features', function() {
      beforeEach(function() {
        var deferred = $q.defer();
        deferred.resolve({data: {project_id: 'abc'}});
        spyOn(keystoneAPI, 'getCurrentUserSession').and.returnValue(deferred.promise);
      });

      it("resolves the promise when project matches", function() {
        factory.isCurrentProject('abc').then(pass, fail);
        $timeout.flush();
      });

      it("rejects the promise when project doesn't match", function() {
        factory.isCurrentProject('abcdef').then(fail, pass);
        $timeout.flush();
      });

      function pass() {
        expect(true).toBe(true);
      }

      function fail() {
        expect(true).toBe(false);
      }

    });

  });

}());
