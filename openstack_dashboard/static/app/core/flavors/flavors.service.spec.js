/*
 * (c) Copyright 2016 Hewlett Packard Enterprise Development LP
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
  "use strict";

  describe('flavors service', function() {
    var service;
    beforeEach(module('horizon.framework.util'));
    beforeEach(module('horizon.framework.conf'));
    beforeEach(module('horizon.app.core.flavors'));
    beforeEach(inject(function($injector) {
      service = $injector.get('horizon.app.core.flavors.service');
    }));

    describe('getFlavorsPromise', function() {
      it("provides a promise that gets translated", inject(function($q, $injector) {
        var glance = $injector.get('horizon.app.core.openstack-service-api.nova');
        var deferred = $q.defer();
        spyOn(glance, 'getFlavors').and.returnValue(deferred.promise);
        service.getFlavorsPromise({});
        deferred.resolve({data: {items: [{id: 1, updated_at: 'jul1'}]}});
        expect(glance.getFlavors).toHaveBeenCalled();
      }));
    });

  });
})();
