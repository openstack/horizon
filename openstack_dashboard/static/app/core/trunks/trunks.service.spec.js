/**
 * Copyright 2017 Ericsson
 *
 * Licensed under the Apache License, Version 2.0 (the "License"); you may
 * not use this file except in compliance with the License. You may obtain
 * a copy of the License at
 *
 *    http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
 * WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
 * License for the specific language governing permissions and limitations
 * under the License.
 */

(function() {
  "use strict";

  describe('trunks service', function() {
    var service;
    beforeEach(module('horizon.framework.util'));
    beforeEach(module('horizon.framework.conf'));
    beforeEach(module('horizon.app.core.trunks'));
    beforeEach(inject(function($injector) {
      service = $injector.get('horizon.app.core.trunks.service');
    }));

    describe('getTrunksPromise', function() {
      it("provides a promise that gets translated", inject(function($q, $injector, $timeout) {
        var neutron = $injector.get('horizon.app.core.openstack-service-api.neutron');
        var session = $injector.get('horizon.app.core.openstack-service-api.userSession');
        var deferred = $q.defer();
        var deferredSession = $q.defer();
        spyOn(neutron, 'getTrunks').and.returnValue(deferred.promise);
        spyOn(session, 'get').and.returnValue(deferredSession.promise);
        var result = service.getTrunksPromise({});
        deferred.resolve({data: {items: [{id: 1, updated_at: 'Apr10'}]}});
        deferredSession.resolve({project_id: '42'});
        $timeout.flush();
        expect(neutron.getTrunks).toHaveBeenCalled();
        expect(result.$$state.value.data.items[0].updated_at).toBe('Apr10');
        expect(result.$$state.value.data.items[0].id).toBe(1);
      }));
    });

  });
})();
