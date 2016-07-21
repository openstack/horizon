/**
 *
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

  describe('horizon.app.core.images.actions.create-volume.service', function() {

    var service, $scope, workflow;
    var wizardModalService = {
      modal: function () {
        return {
          result: angular.noop
        };
      }
    };

    var cinderAPI = {
      createVolume: function(volume) {
        return {
          then: function(callback) {
            callback({data: volume});
          }
        };
      }
    };
    var policyAPI = {
      ifAllowed: function() {
        return {
          success: function(callback) {
            callback({allowed: true});
          }
        };
      }
    };

    var serviceCatalogAPI = {
      ifTypeEnabled: function() {
        return {
          success: function(callback) {
            callback({allowed: true});
          }
        };
      }
    };

    ///////////////////////

    beforeEach(module('horizon.framework'));
    beforeEach(module('horizon.app.core'));
    beforeEach(module('horizon.app.core.images'));

    beforeEach(module(function($provide) {
      $provide.value('horizon.app.core.openstack-service-api.cinder', cinderAPI);
      $provide.value('horizon.app.core.openstack-service-api.policy', policyAPI);
      $provide.value('horizon.app.core.openstack-service-api.serviceCatalog', serviceCatalogAPI);
      $provide.value('horizon.framework.widgets.modal.wizard-modal.service', wizardModalService);
    }));

    beforeEach(inject(function($injector, _$rootScope_) {
      $scope = _$rootScope_.$new();
      service = $injector.get('horizon.app.core.images.actions.create-volume.service');
      workflow = $injector.get('horizon.app.core.images.workflows.create-volume.service');
    }));

    describe('perform', function() {
      it('open the modal with the correct parameters', function() {
        spyOn(wizardModalService, 'modal').and.callThrough();

        var image = {id: '12'};
        service.initAction();
        service.perform(image);

        expect(wizardModalService.modal).toHaveBeenCalled();
        var modalArgs = wizardModalService.modal.calls.argsFor(0)[0];
        expect(modalArgs.data.image).toEqual(image);
        expect(modalArgs.workflow).toEqual(workflow);
        expect(modalArgs.submit).toBeDefined();
      });

      it('should create volume in cinder', function() {
        var volume = { name: 'Test', id: '2' };

        spyOn(cinderAPI, 'createVolume').and.callThrough();
        spyOn(wizardModalService, 'modal').and.callThrough();

        service.initAction();
        service.perform();

        var modalArgs = wizardModalService.modal.calls.argsFor(0)[0];
        modalArgs.submit({volumeForm: volume});
        $scope.$apply();

        expect(cinderAPI.createVolume).toHaveBeenCalledWith(volume);
      });
    });

    describe('allowed', function() {
      it('should allow create volume if image can be launched', function() {
        var image = {container_format: 'ami', status: 'active'};
        var allowed = service.allowed(image);
        permissionShouldPass(allowed);
        $scope.$apply();
      });

      it('should not allow create volume if image is not bootable', function() {
        var image = {container_format: 'ari', status: 'active'};
        var allowed = service.allowed(image);
        permissionShouldFail(allowed);
        $scope.$apply();
      });

      it('should not allow create volume if image status is not active', function() {
        var image = {container_format: 'ari', status: 'not_active'};
        var allowed = service.allowed(image);
        permissionShouldFail(allowed);
        $scope.$apply();
      });

      function permissionShouldFail(permissions) {
        permissions.then(
          function() {
            expect(false).toBe(true);
          },
          function() {
            expect(true).toBe(true);
          });
      }

      function permissionShouldPass(permissions) {
        permissions.then(
          function() {
            expect(true).toBe(true);
          },
          function() {
            expect(false).toBe(true);
          });
      }
    });

  });
})();
