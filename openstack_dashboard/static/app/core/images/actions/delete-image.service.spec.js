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

  describe('horizon.app.core.images.actions.delete-image.service', function() {

    var context = {
      title: gettext('Confirm Delete Images'),
      message: gettext('selected "%s"'),
      submit: gettext('Delete'),
      success: gettext('Deleted : %s.'),
      error: gettext('Unable to delete: %s.')
    };

    var deleteModalService = {
      open: function () {
        return;
      }
    };

    var glanceAPI = {
      deleteImage: function() {
        return;
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

    var deferred, service, $scope;

    ///////////////////////

    beforeEach(module('horizon.app.core'));
    beforeEach(module('horizon.app.core.images'));
    beforeEach(module('horizon.framework'));

    beforeEach(module('horizon.framework.widgets.modal', function($provide) {
      $provide.value('horizon.framework.widgets.modal.deleteModalService', deleteModalService);
    }));

    beforeEach(module('horizon.app.core.openstack-service-api', function($provide) {
      $provide.value('horizon.app.core.openstack-service-api.glance', glanceAPI);
      spyOn(policyAPI, 'ifAllowed').and.callThrough();
      $provide.value('horizon.app.core.openstack-service-api.policy', policyAPI);
      spyOn(userSession, 'isCurrentProject').and.callThrough();
      $provide.value('horizon.app.core.openstack-service-api.userSession', userSession);
    }));

    beforeEach(inject(function($injector, _$rootScope_, $q) {
      $scope = _$rootScope_.$new();
      service = $injector.get('horizon.app.core.images.actions.delete-image.service');
      service.initScope($scope, context);
      deferred = $q.defer();
    }));

    it('should open the delete modal with correct messages', function() {
      var images = [
        {protected: false, owner: 'project', status: 'active', name: 'image1', id: '1'}
      ];

      spyOn(deleteModalService, 'open');

      service.perform(images);
      $scope.$apply();

      expect(deleteModalService.open).toHaveBeenCalled();

      var args = deleteModalService.open.calls.argsFor(0);
      var labels = args[2].labels;

      expect(labels.title).toEqual('Confirm Delete Images');
      expect(labels.message).toEqual('selected "%s"');
      expect(labels.submit).toEqual('Delete');
      expect(labels.success).toEqual('Deleted : %s.');
      expect(labels.error).toEqual('Unable to delete: %s.');
    });

    it('should pass in the success and error events to be thrown', function() {
      var images = [
        {protected: false, owner: 'project', status: 'active', name: 'image1', id: '1'}
      ];

      spyOn(deleteModalService, 'open');

      service.perform(images);
      $scope.$apply();

      expect(deleteModalService.open).toHaveBeenCalled();

      var args = deleteModalService.open.calls.argsFor(0);
      var contextArg = args[2];

      expect(contextArg.successEvent).toEqual('horizon.app.core.images.DELETE_SUCCESS');
    });

    it('should open the delete modal with correct entities', function() {
      var images = [
        {protected: false, owner: 'project', status: 'active', name: 'image1', id: '1'},
        {protected: false, owner: 'project', status: 'active', name: 'image2', id: '2'}
      ];

      spyOn(deleteModalService, 'open');

      service.perform(images);
      $scope.$apply();

      expect(deleteModalService.open).toHaveBeenCalled();

      var args = deleteModalService.open.calls.argsFor(0);
      var entities = args[1];

      expect(entities[0].id).toEqual('1');
      expect(entities[0].name).toEqual('image1');
      expect(entities[1].id).toEqual('2');
      expect(entities[1].name).toEqual('image2');
    });

    it('should only attempt to delete images that are allowed to be deleted', function() {
      var images = [
        {protected: false, owner: 'project', status: 'active', name: 'image1', id: '1'},
        {protected: false, owner: 'project', status: 'active', name: 'image2', id: '2'},
        {protected: false, owner: 'project', status: 'deleted', name: 'image3', id: '3'},
        {protected: false, owner: 'project1', status: 'active', name: 'image4', id: '4'},
        {protected: true, owner: 'project', status: 'active', name: 'image5', id: '5'}
      ];

      spyOn(deleteModalService, 'open');

      service.perform(images);
      $scope.$apply();

      expect(deleteModalService.open).toHaveBeenCalled();

      var args = deleteModalService.open.calls.argsFor(0);
      var entities = args[1];

      expect(entities[0].id).toEqual('1');
      expect(entities[0].name).toEqual('image1');
      expect(entities[1].id).toEqual('2');
      expect(entities[1].name).toEqual('image2');
    });

    it('should not open modal if no images can be deleted', function() {
      var images = [
        {protected: false, owner: 'project', status: 'deleted', name: 'image3', id: '3'},
        {protected: false, owner: 'project1', status: 'active', name: 'image4', id: '4'},
        {protected: true, owner: 'project', status: 'active', name: 'image5', id: '5'}
      ];

      spyOn(deleteModalService, 'open');

      deferred.reject();
      service.initScope($scope, context);
      service.perform(images);
      $scope.$apply();

      expect(deleteModalService.open).not.toHaveBeenCalled();
    });

    it('should pass in a function that deletes an image', function() {
      var image = {protected: false, owner: 'project', status: 'active', name: 'image1', id: '1'};

      spyOn(deleteModalService, 'open');
      spyOn(glanceAPI, 'deleteImage');

      service.perform([image]);
      $scope.$apply();

      var contextArg = deleteModalService.open.calls.argsFor(0)[2];
      var deleteFunction = contextArg.deleteEntity;

      deleteFunction(image.id);

      expect(glanceAPI.deleteImage).toHaveBeenCalledWith(image.id, true);
    });

    it('should allow delete if image can be deleted', function() {
      var image = {protected: false, owner: 'project', status: 'active'};
      permissionShouldPass(service.allowed(image));
      $scope.$apply();
    });

    it('should not allow delete if image is protected', function() {
      var image = {protected: true, owner: 'project', status: 'active'};
      permissionShouldFail(service.allowed(image));
      $scope.$apply();
    });

    it('should not allow delete if image is not owned by user', function() {
      var image = {protected: false, owner: 'another_project', status: 'active'};
      deferred.reject();
      permissionShouldFail(service.allowed(image));
      $scope.$apply();
    });

    it('should not allow delete if image status is deleted', function() {
      var image = {protected: false, owner: 'project', status: 'deleted'};
      permissionShouldFail(service.allowed(image));
      $scope.$apply();
    });

    function permissionShouldPass(permissions) {
      permissions.then(
        function() {
          expect(true).toBe(true);
        },
        function() {
          expect(false).toBe(true);
        });
    }

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

})();
