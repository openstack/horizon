/**
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

  describe('horizon.app.core.keypairs.actions.create.service', function() {

    var service, nova, $q, $scope, deferred, deferredKeypairs, deferredNewKeypair, toast;
    var model = {
      name: "Hiroshige"
    };
    var modal = {
      open: function (config) {
        config.model = model;
        deferred = $q.defer();
        deferred.resolve(config);
        return deferred.promise;
      }
    };

    ///////////////////

    beforeEach(module('horizon.app.core'));
    beforeEach(module('horizon.framework'));
    beforeEach(module('horizon.app.core.keypairs.actions'));

    beforeEach(module(function($provide) {
      $provide.value('horizon.framework.widgets.form.ModalFormService', modal);
    }));

    beforeEach(inject(function($injector, _$rootScope_, _$q_) {
      $scope = _$rootScope_.$new();
      $q = _$q_;
      service = $injector.get('horizon.app.core.keypairs.actions.create.service');
      nova = $injector.get('horizon.app.core.openstack-service-api.nova');
      toast = $injector.get('horizon.framework.widgets.toast.service');
      deferredKeypairs = $q.defer();
      deferredKeypairs.resolve({data: {items: [{keypair: {name: "Hokusai"}}]}});
      spyOn(nova, 'getKeypairs').and.returnValue(deferredKeypairs.promise);
      deferredNewKeypair = $q.defer();
      deferredNewKeypair.resolve({data: {items: [{keypair: {name: "Hiroshige"}}]}});
      spyOn(nova, 'createKeypair').and.returnValue(deferredNewKeypair.promise);
      spyOn(modal, 'open').and.callThrough();
      spyOn(toast, 'add').and.callFake(angular.noop);
    }));

    it('should check the policy if the user is allowed to create key pair', function() {
      var allowed = service.allowed();
      expect(allowed).toBeTruthy();
    });

    it('should open the modal and submit', inject(function() {
      service.perform();
      expect(nova.getKeypairs).toHaveBeenCalled();
      expect(modal.open).toHaveBeenCalled();

      $scope.$apply();
      expect(nova.createKeypair).toHaveBeenCalled();
      expect(toast.add).toHaveBeenCalled();
    }));
  });
})();
