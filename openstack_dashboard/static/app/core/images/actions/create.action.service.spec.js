/**
 * (c) Copyright 2016 Hewlett-Packard Development Company, L.P.
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
  'use strict';

  describe('horizon.app.core.images.actions.create.service', function() {
    var metadataService = {
      editMetadata: function() {
        return {
          then: function(callback) {
            callback();
          }
        };
      }
    };

    var wizardModalService = {
      modal: function (config) {
        deferredModal = $q.defer();
        deferredModal.resolve(config.scope.image);
        return {result: deferredModal.promise};
      }
    };

    var glanceAPI = {
      createImage: function(image) {
        deferredCreate = $q.defer();
        deferredCreate.resolve({data: image});
        return deferredCreate.promise;
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

    var service, events, $scope, toast, deferredModal, deferredCreate, $q;

    ///////////////////////

    beforeEach(module('horizon.app.core'));
    beforeEach(module('horizon.framework'));

    beforeEach(module(function($provide) {
      $provide.value('horizon.framework.widgets.modal.wizard-modal.service', wizardModalService);
      $provide.value('horizon.app.core.openstack-service-api.glance', glanceAPI);
      $provide.value('horizon.app.core.openstack-service-api.policy', policyAPI);
      $provide.value('horizon.app.core.metadata.service', metadataService);
    }));

    beforeEach(inject(function($injector, _$rootScope_, _$q_) {
      $scope = _$rootScope_.$new();
      service = $injector.get('horizon.app.core.images.actions.create.service');
      events = $injector.get('horizon.app.core.images.events');
      toast = $injector.get('horizon.framework.widgets.toast.service');
      $q = _$q_;
    }));

    it('should check the policy if the user is allowed to delete images', function() {
      spyOn(policyAPI, 'ifAllowed').and.callThrough();
      var allowed = service.allowed();
      expect(allowed).toBeTruthy();
      expect(policyAPI.ifAllowed).toHaveBeenCalledWith({ rules: [['image', 'add_image']] });
    });

    it('open the modal with the correct parameters', function() {
      spyOn(wizardModalService, 'modal').and.callThrough();

      service.initScope($scope);
      service.perform();

      expect(wizardModalService.modal).toHaveBeenCalled();
      expect($scope.image).toEqual({});

      var modalArgs = wizardModalService.modal.calls.argsFor(0)[0];
      expect(modalArgs.scope).toEqual($scope);
      expect(modalArgs.workflow).toBeDefined();
      expect(modalArgs.submit).toBeDefined();
    });

    it('should submit create image request to glance', function() {
      var image = { name: 'Test', id: '2' };
      var newMetadata = {prop1: '11', prop3: '3'};

      spyOn($scope, '$emit').and.callThrough();
      spyOn(glanceAPI, 'createImage').and.callThrough();
      spyOn(toast, 'add').and.callThrough();
      spyOn(wizardModalService, 'modal').and.callThrough();

      service.initScope($scope);
      service.perform();

      $scope.$emit(events.IMAGE_CHANGED, image);
      $scope.$emit(events.IMAGE_METADATA_CHANGED, newMetadata);

      var modalArgs = wizardModalService.modal.calls.argsFor(0)[0];
      modalArgs.submit();
      $scope.$apply();

      expect(glanceAPI.createImage).toHaveBeenCalledWith({ name: 'Test',
        id: '2', prop1: '11', prop3: '3'});
      expect(toast.add).toHaveBeenCalledWith('success', 'Image Test was successfully created.');
    });

    it('should raise event even if update meta data fails', function() {
      var image = { name: 'Test', id: '2' };
      var failedPromise = function() {
        return {
          then: function(callback, errorCallback) {
            errorCallback();
          }
        };
      };

      spyOn(wizardModalService, 'modal').and.callThrough();
      spyOn(glanceAPI, 'createImage').and.callThrough();
      spyOn(metadataService, 'editMetadata').and.callFake(failedPromise);
      spyOn($scope, '$emit').and.callThrough();
      spyOn(toast, 'add').and.callThrough();

      service.initScope($scope);
      service.perform();
      $scope.$apply();

      $scope.$emit(events.IMAGE_CHANGED, image);
      $scope.$emit(events.IMAGE_METADATA_CHANGED, newMetadata);

      var newMetadata = {prop1: '11', prop3: '3'};
      var modalArgs = wizardModalService.modal.calls.argsFor(0)[0];
      modalArgs.submit();
      $scope.$apply();

      expect(toast.add.calls.count()).toBe(1);
    });

    it('should destroy the event watchers', function() {
      var newImage = { name: 'Test2', id: '2' };
      var newMetadata = {p1: '11', p3: '3'};

      spyOn(wizardModalService, 'modal').and.callThrough();
      spyOn(glanceAPI, 'createImage').and.callThrough();
      spyOn(metadataService, 'editMetadata').and.callThrough();
      spyOn(toast, 'add').and.callThrough();

      service.initScope($scope);
      service.perform();
      $scope.$apply();

      $scope.$emit('$destroy');
      $scope.$emit(events.IMAGE_CHANGED, newImage);
      $scope.$emit(events.IMAGE_METADATA_CHANGED, newMetadata);

      var modalArgs = wizardModalService.modal.calls.argsFor(0)[0];
      modalArgs.submit();
      $scope.$apply();

      expect(glanceAPI.createImage).toHaveBeenCalledWith({});
      expect(toast.add.calls.count()).toBe(1);
    });

  });

})();
