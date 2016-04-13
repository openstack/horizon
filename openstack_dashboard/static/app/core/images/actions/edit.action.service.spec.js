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

  describe('horizon.app.core.images.actions.edit.service', function() {
    var existingMetadata = {p1: '1', p2: '2'};

    var metadataService = {
      getMetadata: function() {
        return {
          then: function(callback) {
            callback({
              data: existingMetadata
            });
          }
        };
      },
      editMetadata: function() {
        return {
          then: function(callback) {
            callback();
          }
        };
      }
    };

    var wizardModalService = {
      modal: function () {
        return { result: {} };
      }
    };

    var glanceAPI = {
      updateImage: function(image) {
        return {
          then: function(callback) {
            callback({data: image});
          }
        };
      },
      getImage: function() {
        var imageLoad = $q.defer();
        imageLoad.resolve({data: testImage});
        return imageLoad.promise;
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

    var userSession = {
      isCurrentProject: function() {
        deferred.resolve();
        return deferred.promise;
      }
    };

    var service, events, $scope, $q, toast, deferred, testImage, $timeout;

    ///////////////////////

    beforeEach(module('horizon.framework'));
    beforeEach(module('horizon.app.core'));

    beforeEach(module(function($provide) {
      $provide.value('horizon.app.core.openstack-service-api.glance', glanceAPI);
      $provide.value('horizon.app.core.openstack-service-api.userSession', userSession);
      $provide.value('horizon.app.core.openstack-service-api.policy', policyAPI);
      $provide.value('horizon.app.core.metadata.service', metadataService);
      $provide.value('horizon.framework.widgets.modal.wizard-modal.service', wizardModalService);
    }));

    beforeEach(inject(function($injector, _$rootScope_, _$q_, _$timeout_) {
      $scope = _$rootScope_.$new();
      $q = _$q_;
      service = $injector.get('horizon.app.core.images.actions.edit.service');
      events = $injector.get('horizon.app.core.images.events');
      toast = $injector.get('horizon.framework.widgets.toast.service');
      service.initScope($scope);
      deferred = $q.defer();
      $timeout = _$timeout_;
    }));

    describe('perform', function() {
      it('should open the modal with the correct parameters', function() {
        spyOn(wizardModalService, 'modal').and.callThrough();

        testImage = {id: '12'};
        service.initScope($scope);
        service.perform(testImage);
        $timeout.flush();

        expect(wizardModalService.modal).toHaveBeenCalled();
        expect($scope.imagePromise).toBeDefined();

        var modalArgs = wizardModalService.modal.calls.argsFor(0)[0];
        expect(modalArgs.scope).toEqual($scope);
        expect(modalArgs.workflow).toBeDefined();
      });

      it('should update image in glance, update metadata and raise event', function() {
        testImage = { name: 'Test', id: '2' };
        var newImage = { name: 'Test2', id: '2' };
        var newMetadata = {p1: '11', p3: '3'};

        spyOn($scope, '$emit').and.callThrough();
        spyOn(glanceAPI, 'updateImage').and.callThrough();
        spyOn(metadataService, 'editMetadata').and.callThrough();
        spyOn(toast, 'add').and.callThrough();
        spyOn(wizardModalService, 'modal').and.callThrough();

        service.initScope($scope);
        service.perform(testImage);
        $timeout.flush();

        $scope.$emit(events.IMAGE_CHANGED, newImage);
        $scope.$emit(events.IMAGE_METADATA_CHANGED, newMetadata);

        var modalArgs = wizardModalService.modal.calls.argsFor(0)[0];
        modalArgs.submit();
        $scope.$apply();

        expect(glanceAPI.updateImage).toHaveBeenCalledWith(newImage);
        expect(metadataService.editMetadata)
          .toHaveBeenCalledWith('image', '2', newMetadata, ['p2']);
        expect(toast.add)
          .toHaveBeenCalledWith('success', 'Image Test2 was successfully updated.');
        expect(toast.add.calls.count()).toBe(2);
        expect($scope.$emit)
          .toHaveBeenCalledWith('horizon.app.core.images.UPDATE_SUCCESS', newImage);
      });

      it('should raise event even if update meta data fails', function() {
        var image = { name: 'Test', id: '2' };
        var newImage = { name: 'Test2', id: '2' };
        var newMetadata = {prop1: '11', prop3: '3'};

        var failedPromise = function() {
          return {
            then: function(callback, errorCallback) {
              errorCallback();
            }
          };
        };

        spyOn(wizardModalService, 'modal').and.callThrough();
        spyOn(glanceAPI, 'updateImage').and.callThrough();
        spyOn(metadataService, 'editMetadata').and.callFake(failedPromise);
        spyOn($scope, '$emit').and.callThrough();
        spyOn(toast, 'add').and.callThrough();

        service.initScope($scope);
        service.perform(image);
        $scope.$apply();

        $scope.$emit(events.IMAGE_CHANGED, newImage);
        $scope.$emit(events.IMAGE_METADATA_CHANGED, newMetadata);

        var modalArgs = wizardModalService.modal.calls.argsFor(0)[0];
        modalArgs.submit();
        $scope.$apply();

        expect(toast.add.calls.count()).toBe(1);
        expect($scope.$emit)
          .toHaveBeenCalledWith('horizon.app.core.images.UPDATE_SUCCESS', newImage);
      });

      it('should destroy the event watchers', function() {
        testImage = { name: 'Test', id: '2' };
        var newImage = { name: 'Test2', id: '2' };
        var newMetadata = {p1: '11', p3: '3'};

        spyOn(wizardModalService, 'modal').and.callThrough();
        spyOn(glanceAPI, 'updateImage').and.callThrough();
        spyOn(metadataService, 'editMetadata').and.callThrough();
        spyOn(toast, 'add').and.callThrough();

        service.initScope($scope);
        service.perform(testImage);
        $scope.$apply();

        $scope.$emit('$destroy');
        $scope.$emit(events.IMAGE_CHANGED, newImage);
        $scope.$emit(events.IMAGE_METADATA_CHANGED, newMetadata);

        var modalArgs = wizardModalService.modal.calls.argsFor(0)[0];
        modalArgs.submit();
        $scope.$apply();

        expect(glanceAPI.updateImage).toHaveBeenCalledWith(testImage);
        expect(metadataService.editMetadata)
          .toHaveBeenCalledWith('image', testImage.id, {}, ['p1', 'p2']);
        expect(toast.add.calls.count()).toBe(2);
      });
    });

    describe('edit', function() {
      it('should allow edit if image can be edited', function() {
        var image = {owner: 'project', status: 'active'};
        var allowed = service.allowed(image);
        permissionShouldPass(allowed);
        $scope.$apply();
      });

      it('should not allow edit if image is not owned by user', function() {
        deferred.reject();
        var image = {owner: 'doesnt_matter', status: 'active'};
        var allowed = service.allowed(image);
        permissionShouldFail(allowed);
        $scope.$apply();
      });

      it('should not allow edit if image status is not active', function() {
        var image = {owner: 'project', status: 'not_active'};
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
