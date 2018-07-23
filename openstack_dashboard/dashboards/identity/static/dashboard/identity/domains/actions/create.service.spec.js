/**
 * Licensed under the Apache License, Version 2.0 (the "License"); you may
 * not use self file except in compliance with the License. You may obtain
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

  describe('horizon.dashboard.identity.domains.actions.create.service', function() {

    var service, $scope, $q, modal, keystoneAPI, policyAPI;
    var createDomainResponse = {
      data: {
        id: '1234',
        name: 'test',
        description: 'desc',
        enabled: true
      }
    };

    beforeEach(module('horizon.framework'));
    beforeEach(module('horizon.app.core'));
    beforeEach(module('horizon.dashboard.identity.domains'));

    beforeEach(inject(function($injector, _$rootScope_, _$q_) {
      $scope = _$rootScope_.$new();
      $q = _$q_;

      keystoneAPI = $injector.get('horizon.app.core.openstack-service-api.keystone');
      policyAPI = $injector.get('horizon.app.core.openstack-service-api.policy');
      modal = $injector.get('horizon.framework.widgets.form.ModalFormService');
      service = $injector.get('horizon.dashboard.identity.domains.actions.create.service');
    }));

    describe('should open the modal', function() {
      it('open the modal', function() {
        var deferred = $q.defer();
        deferred.resolve(true);
        spyOn(modal, "open").and.returnValue($q.defer().promise);

        service.perform();
        $scope.$apply();

        expect(modal.open).toHaveBeenCalled();
      });

      it('should call keystone.createDomain', function() {
        var deferred = $q.defer();
        deferred.resolve(true);
        spyOn(modal, "open").and.returnValue(deferred.promise);

        var deferredCreateDomain = $q.defer();
        deferredCreateDomain.resolve(createDomainResponse);
        spyOn(keystoneAPI, 'createDomain').and.returnValue(deferredCreateDomain.promise);

        service.perform();
        $scope.$apply();

        expect(keystoneAPI.createDomain).toHaveBeenCalled();
      });
    });

    describe('allowed', function() {
      it('should allow create domain', function() {
        var deferred = $q.defer();
        deferred.resolve(true);
        spyOn(policyAPI, 'ifAllowed').and.returnValue(deferred.promise);
        var deferredCanEdit = $q.defer();
        deferredCanEdit.resolve(true);
        spyOn(keystoneAPI, 'canEditIdentity').and.returnValue(deferredCanEdit.promise);

        var allowed = service.allowed();

        expect(allowed).toBeTruthy();
        expect(keystoneAPI.canEditIdentity).toHaveBeenCalledWith('domain');
        expect(policyAPI.ifAllowed).toHaveBeenCalledWith(
          { rules: [['identity', 'create_domain']] });
      });
    });
  });
})();
