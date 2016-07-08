/*
 * (c) Copyright 2016 Hewlett-Packard Development Company, L.P.
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

  describe('permissions service', function() {
    var service;

    beforeEach(module('horizon.framework.conf'));
    beforeEach(inject(function($injector) {
      service = $injector.get('horizon.framework.conf.permissions.service');
    }));

    it("is defined", function() {
      expect(service).toBeDefined();
    });

    describe("checkAllowed", function() {

      it("returns rejected promise returned by configItem.allowed", inject(function($q, $timeout) {
        var deferred = $q.defer();
        deferred.reject();
        var item = {allowed: function() { return deferred.promise; }};
        service.checkAllowed(item).then(fail, pass);
        $timeout.flush();
      }));

      it("returns resolved promise returned by configItem.allowed", inject(function($q, $timeout) {
        var deferred = $q.defer();
        deferred.resolve({});
        var item = {allowed: function() { return deferred.promise; }};
        service.checkAllowed(item).then(pass, fail);
        $timeout.flush();
      }));

      it("returns resolved promise when no configItem.allowed", inject(function($q, $timeout) {
        var item = {};
        service.checkAllowed(item).then(pass, fail);
        $timeout.flush();
      }));

    });

    describe("checkAll", function() {
      describe("with extended permissions", function() {
        beforeEach(inject(function($q) {
          var resolver = function() { return $q.defer().promise; };
          service.extendedPermissions = { perm1: resolver };
        }));

        it("with promise array, adds checks for permissions", inject(function($q) {
          var input = {perm1: [$q.defer().promise]};
          service.checkAll(input).then(verifyResult);
          function verifyResult(result) {
            expect(angular.isArray(result)).toBe(true);
            expect(result.length).toBe(1);
          }
        }));

        it("with promise, adds checks for permissions", inject(function($q) {
          var input = {perm1: $q.defer().promise};
          service.checkAll(input).then(verifyResult);
          function verifyResult(result) {
            expect(angular.isArray(result)).toBe(true);
            expect(result.length).toBe(1);
          }
        }));

        it("with no promise, adds checks for permissions", inject(function($q) {
          var input = {unlisted: $q.defer().promise};
          service.checkAll(input).then(verifyResult);
          function verifyResult(result) {
            expect(angular.isArray(result)).toBe(true);
            expect(result.length).toBe(1);
          }
        }));
      });

      it("without extended permissions it returns no promises", inject(function($q) {
        var retval = service.checkAll({perm1: [$q.defer().promise]});
        retval.then(verifyResult);
        function verifyResult(result) {
          expect(angular.isArray(result)).toBe(true);
          expect(result.length).toBe(0);
        }
      }));
    });

    describe("extendedPermissions", function() {
      it("defaults to returning no permissions", function() {
        expect(service.extendedPermissions()).toEqual({});
      });

    });

  });

  function pass() {
    expect(true).toBe(true);
  }

  function fail() {
    expect(true).toBe(false);
  }
})();
