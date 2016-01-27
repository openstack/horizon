/**
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

  describe("neutronExtensions", function() {
    var factory, q, neutron;

    beforeEach(module('horizon.app.core.openstack-service-api'));

    beforeEach(module(function($provide) {
      neutron = {getExtensions: function() {return {then: angular.noop}; }};
      q = {defer: function() { return {resolve: angular.noop}; }};
      $provide.value('$cacheFactory', function() {return "cache"; });
      $provide.value('$q', q);
      $provide.value('horizon.app.core.openstack-service-api.neutron', neutron);
    }));

    beforeEach(inject(function($injector) {
      factory = $injector.get('horizon.app.core.openstack-service-api.neutronExtensions');
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
      spyOn(neutron, 'getExtensions').and.returnValue(postAction);
      spyOn(postAction, 'then');
      factory.get();
      expect(neutron.getExtensions).toHaveBeenCalledWith({cache: factory.cache});
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
      expect(deferred.reject).toHaveBeenCalledWith('Cannot get the extension list.');
    });
  });

})();
