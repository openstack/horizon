/*
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
  'use strict';

  describe('keypair details controller', function() {

    var ctrl, deferred, nova;

    beforeEach(module('horizon.app.core.keypairs'));

    beforeEach(inject(function($controller, $q, $injector) {
      nova = $injector.get('horizon.app.core.openstack-service-api.nova');
      deferred = $q.defer();
      deferred.resolve({data: {name: 1}});
      spyOn(nova, 'getKeypair').and.returnValue(deferred.promise);
      ctrl = $controller('horizon.app.core.keypairs.DetailsController',
        {
          '$scope' : {context : {loadPromise: deferred.promise}}
        }
      );
    }));

    it('sets ctrl', inject(function($timeout) {
      $timeout.flush();
      expect(ctrl.keypair).toBeDefined();
    }));

  });
})();
