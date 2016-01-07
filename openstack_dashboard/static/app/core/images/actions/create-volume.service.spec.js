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

    var service, $scope, toast, events, workflow;
    var wizardModalService = {
      modal: function () {}
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
      toast = $injector.get('horizon.framework.widgets.toast.service');
      events = $injector.get('horizon.app.core.images.events');
      workflow = $injector.get('horizon.app.core.images.workflows.create-volume.service');
    }));

    describe('perform', function() {
      it('open the modal with the correct parameters', function() {
        spyOn(wizardModalService, 'modal').and.callThrough();

        var image = {id: '12'};
        service.initScope($scope);
        service.perform(image);

        expect(wizardModalService.modal).toHaveBeenCalled();
        var modalArgs = wizardModalService.modal.calls.argsFor(0)[0];
        expect(modalArgs.scope).toEqual($scope);
        expect(modalArgs.workflow).toEqual(workflow);
        expect(modalArgs.submit).toBeDefined();
      });

      it('should create volume in cinder and raise event', function() {
        var volume = { name: 'Test', id: '2' };

        spyOn(cinderAPI, 'createVolume').and.callThrough();
        spyOn(toast, 'add').and.callThrough();
        spyOn(wizardModalService, 'modal').and.callThrough();

        service.initScope($scope);
        service.perform();

        $scope.$emit(events.VOLUME_CHANGED, volume);
        $scope.$apply();

        var modalArgs = wizardModalService.modal.calls.argsFor(0)[0];
        modalArgs.submit();
        $scope.$apply();

        expect(cinderAPI.createVolume).toHaveBeenCalledWith(volume);
        expect(toast.add).toHaveBeenCalledWith('success', 'Volume Test was successfully created.');
        expect(toast.add.calls.count()).toBe(1);
      });

      it('should destroy volume change watcher on exit', function() {
        spyOn(cinderAPI, 'createVolume').and.callThrough();
        spyOn(wizardModalService, 'modal').and.callThrough();

        service.initScope($scope);
        service.perform();

        var oldVolume = {id: 1};
        $scope.$emit(events.VOLUME_CHANGED, oldVolume);

        $scope.$emit('$destroy');

        var newVolume = {id: 2};
        $scope.$emit(events.VOLUME_CHANGED, newVolume);

        var modalArgs = wizardModalService.modal.calls.argsFor(0)[0];
        modalArgs.submit();

        expect(cinderAPI.createVolume).toHaveBeenCalledWith(oldVolume);
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
