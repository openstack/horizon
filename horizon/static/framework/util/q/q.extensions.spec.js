/*
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

  describe('horizon.framework.util.q.extensions', function () {

    describe('allSettled', function() {
      var service, $q, $scope;

      var failedPromise = function() {
        var deferred2 = $q.defer();
        deferred2.reject('failed');
        return deferred2.promise;
      };

      var passedPromise = function() {
        var deferred1 = $q.defer();
        deferred1.resolve('passed');
        return deferred1.promise;
      };

      beforeEach(module('horizon.framework.util.q'));
      beforeEach(inject(function($injector, _$rootScope_) {
        service = $injector.get('horizon.framework.util.q.extensions');
        $q = $injector.get('$q');
        $scope = _$rootScope_.$new();
      }));

      it('should define allSettled', function () {
        expect(service.allSettled).toBeDefined();
      });

      it('should resolve all given promises', function() {
        service.allSettled([{
          promise: failedPromise(),
          context: '1'
        }, {
          promise: passedPromise(),
          context: '2'
        }]).then(onAllSettled);

        $scope.$apply();

        function onAllSettled(resolvedPromises) {
          expect(resolvedPromises.fail.length).toEqual(1);
          expect(resolvedPromises.fail[0]).toEqual({data: 'failed', context: '1'});
          expect(resolvedPromises.pass.length).toEqual(1);
          expect(resolvedPromises.pass[0]).toEqual({data: 'passed', context: '2'});
        }
      });

      it('should maintain order of promises regardless of resolve/reject order', function() {
        var defs = [$q.defer(), $q.defer(), $q.defer(), $q.defer(), $q.defer(), $q.defer()];
        service.allSettled([{
          promise: defs[0].promise,
          context: '1'
        },{
          promise: defs[1].promise,
          context: '2'
        },{
          promise: defs[2].promise,
          context: '3'
        },{
          promise: defs[3].promise,
          context: '4'
        },{
          promise: defs[4].promise,
          context: '5'
        },{
          promise: defs[5].promise,
          context: '6'
        }]).then(onAllSettled);

        defs[1].reject();
        defs[2].resolve();
        defs[0].resolve();
        defs[5].reject();
        defs[3].reject();
        defs[4].resolve();

        $scope.$apply();

        function onAllSettled(resolvedPromises) {
          var pass = resolvedPromises.pass;
          var fail = resolvedPromises.fail;
          expect(pass.length).toBe(3);
          expect(fail.length).toBe(3);
          expect(pass[0].context).toBe('1');
          expect(pass[1].context).toBe('3');
          expect(pass[2].context).toBe('5');
          expect(fail[0].context).toBe('2');
          expect(fail[1].context).toBe('4');
          expect(fail[2].context).toBe('6');
        }
      });
    });

    describe('booleanAsPromise', function() {
      var service, $scope;

      beforeEach(module('horizon.framework.util.q'));
      beforeEach(inject(function($injector, _$rootScope_) {
        service = $injector.get('horizon.framework.util.q.extensions');
        $scope = _$rootScope_.$new();
      }));

      it('should define booleanAsPromise', function () {
        expect(service.booleanAsPromise).toBeDefined();
      });

      it('should reject the promise if condition does not evaluates to true', function() {
        var testValues = [ false, null, {}, 'A', 7 ];
        var rejectCount = 0;
        testValues.map(function doTest(testValue) {
          service.booleanAsPromise(testValue).then(angular.noop, function failTest() {
            rejectCount++;
          });
          $scope.$apply();
        });
        expect(rejectCount).toEqual(testValues.length);
      });

      it('should resolve the promise only if condition to true', function() {
        var passCount = 0;
        service.booleanAsPromise(true).then(function passTest() {
          passCount++;
        });
        $scope.$apply();
        expect(passCount).toEqual(1);
      });
    });
  });

})();
