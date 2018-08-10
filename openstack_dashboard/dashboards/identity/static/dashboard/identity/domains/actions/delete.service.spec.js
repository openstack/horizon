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

  describe('horizon.dashboard.identity.domains.actions.delete.service', function() {

    var service, $scope, deferredModal, deferredPolicy;

    var deleteModalService = {
      onlyPass: false,
      open: function () {
        var res = {
          pass: [{context: {id: 'a'}}],
          fail: []
        };
        if (!deleteModalService.onlyPass) {
          res.fail.push({context: {id: 'b'}});
        }
        deferredModal.resolve(res);
        return deferredModal.promise;
      }
    };

    var keystoneAPI = {
      deleteDomain: function() {
        return;
      },
      canEditIdentity: function() {
        return;
      }
    };

    var policyAPI = {
      isResolve: true,
      ifAllowed: function() {
        success();

        function success() {
          if (policyAPI.isResolve) {
            deferredPolicy.resolve();
          } else {
            deferredPolicy.reject();
          }
        }
        return deferredPolicy.promise;
      }
    };

    function generateDomains(count) {
      var domains = [];
      for (var i = 0; i < count; i++) {
        domains.push({ name: 'delete_test', id: i + 1});
      }
      return domains;
    }

    beforeEach(module('horizon.dashboard.identity.domains'));
    beforeEach(module('horizon.framework'));
    beforeEach(module('horizon.app.core'));

    beforeEach(module('horizon.framework.widgets.modal', function($provide) {
      $provide.value('horizon.framework.widgets.modal.deleteModalService', deleteModalService);
    }));

    beforeEach(module('horizon.app.core.openstack-service-api', function($provide) {
      $provide.value('horizon.app.core.openstack-service-api.keystone', keystoneAPI);
      $provide.value('horizon.app.core.openstack-service-api.policy', policyAPI);
      spyOn(policyAPI, 'ifAllowed').and.callThrough();
    }));

    beforeEach(inject(function($injector, _$rootScope_, $q) {
      $scope = _$rootScope_.$new();
      service = $injector.get('horizon.dashboard.identity.domains.actions.delete.service');
      deferredModal = $q.defer();
      deferredPolicy = $q.defer();
    }));

    describe('perform method and pass only', function() {
      it('should open the delete modal', function() {
        spyOn(deleteModalService, 'open').and.callThrough();
        spyOn(keystoneAPI, 'deleteDomain');
        deleteModalService.onlyPass = true;

        var domain = generateDomains(1)[0];
        service.perform(domain);
        $scope.$apply();

        var contextArg = deleteModalService.open.calls.argsFor(0)[2];
        var deleteFunction = contextArg.deleteEntity;

        deleteFunction(domain.id);
      });

      it('should pass and fail in a function that delete domain by item action', function() {
        spyOn(deleteModalService, 'open').and.callThrough();
        spyOn(keystoneAPI, 'deleteDomain');
        deleteModalService.onlyPass = false;

        var domain = generateDomains(1)[0];
        service.perform(domain);
        $scope.$apply();

        var contextArg = deleteModalService.open.calls.argsFor(0)[2];
        var deleteFunction = contextArg.deleteEntity;

        deleteFunction(domain.id);
      });

      it('should pass and fail in a function that delete domain by batch action', function() {
        spyOn(deleteModalService, 'open').and.callThrough();
        spyOn(keystoneAPI, 'deleteDomain');
        deleteModalService.onlyPass = false;

        var domain = generateDomains(1)[0];
        service.perform([domain]);
        $scope.$apply();

        var contextArg = deleteModalService.open.calls.argsFor(0)[2];
        var deleteFunction = contextArg.deleteEntity;

        deleteFunction(domain.id);
      });

      it('fail to policy check because of no privilege', function() {
        spyOn(deleteModalService, 'open').and.callThrough();
        spyOn(keystoneAPI, 'deleteDomain');
        spyOn(keystoneAPI, 'canEditIdentity');
        policyAPI.isResolve = false;

        var domain = generateDomains(1)[0];
        service.perform(domain);
        $scope.$apply();

        expect(deleteModalService.open).not.toHaveBeenCalled();
      });
    });
  });
})();
