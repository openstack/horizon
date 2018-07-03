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

  describe('horizon.app.core.images.actions.edit.service', function() {
    var service, $scope, $q, deferred, $timeout, updateImageDeferred;
    var image = {id: 1, name: 'Original', properties: {description: 'bla-bla'}};
    var existingMetadata = {p1: '1', p2: '2'};

    var metadataService = {
      getMetadata: function() {
        return {
          then: function(callback) {
            return callback({
              data: existingMetadata
            });
          }
        };
      },
      editMetadata: function() {
        return {
          then: function(callback) {
            return callback();
          }
        };
      }
    };

    var wizardModalService = {
      modal: function () {
        return { result: {catch: angular.noop} };
      }
    };

    var glanceAPI = {
      updateImage: function() {
        return updateImageDeferred.promise;
      },
      getImage: function() {
        var imageLoad = $q.defer();
        imageLoad.resolve({data: image});
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
      deferred = $q.defer();
      updateImageDeferred = $q.defer();
      $timeout = _$timeout_;
    }));

    describe('perform', function() {
      it('should open the modal with the correct parameters', function() {
        spyOn(wizardModalService, 'modal').and.callThrough();

        service.perform(image, $scope);
        $timeout.flush();

        expect(wizardModalService.modal).toHaveBeenCalled();

        var modalArgs = wizardModalService.modal.calls.argsFor(0)[0];
        expect(modalArgs.workflow).toBeDefined();
      });

      it('should not allow edit if image status is not active', function() {
        var image = {owner: 'project', status: 'not_active'};
        var allowed = service.allowed(image);
        permissionShouldFail(allowed);
        $scope.$apply();
      });

      describe('submit', function() {

        beforeEach(function() {
          spyOn(glanceAPI, 'updateImage').and.callThrough();
          spyOn(wizardModalService, 'modal').and.callThrough();

          service.perform(image, $scope);

          $timeout.flush();
        });

        it('passes the image from the model to updateImage', function() {
          var modalArgs = wizardModalService.modal.calls.argsFor(0)[0];
          modalArgs.submit({imageForm: image});

          updateImageDeferred.resolve();
          $timeout.flush();
          expect(glanceAPI.updateImage.calls.argsFor(0)[0]).toEqual(image);
        });

        it('returns a failed result if API call fails', function() {
          var modalArgs = wizardModalService.modal.calls.argsFor(0)[0];
          var result = modalArgs.submit({imageForm: image});
          updateImageDeferred.reject();
          result.then(function err(data) {
            expect(data.failed.length).toBe(1);
          });
          $timeout.flush();
        });
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

    });

  });

})();
