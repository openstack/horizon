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

    var deleteModalService = {
      open: function () {
        deferredModal.resolve({
          pass: [{context: {id: 'a'}}],
          fail: [{context: {id: 'b'}}]
        });
        return deferredModal.promise;
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

    var deferred, service, $scope, deferredModal;

    ///////////////////////

    beforeEach(module('horizon.app.core'));
    beforeEach(module('horizon.app.core.images'));
    beforeEach(module('horizon.framework'));

    beforeEach(module('horizon.framework.widgets.modal', function($provide) {
      $provide.value('horizon.framework.widgets.modal.deleteModalService', deleteModalService);
    }));

    beforeEach(module('horizon.app.core.openstack-service-api', function($provide) {
      $provide.value('horizon.app.core.openstack-service-api.glance', glanceAPI);
      $provide.value('horizon.app.core.openstack-service-api.policy', policyAPI);
      $provide.value('horizon.app.core.openstack-service-api.userSession', userSession);
      spyOn(policyAPI, 'ifAllowed').and.callThrough();
      spyOn(userSession, 'isCurrentProject').and.callThrough();
    }));

    beforeEach(inject(function($injector, _$rootScope_, $q) {
      $scope = _$rootScope_.$new();
      service = $injector.get('horizon.app.core.images.actions.delete-image.service');
      deferred = $q.defer();
      deferredModal = $q.defer();
    }));

    function generateImage(imageCount) {

      var images = [];
      var data = {
        protected: false,
        owner: 'project',
        status: 'active',
        name: 'image1',
        id: '1'
      };

      for (var index = 0; index < imageCount; index++) {
        var image = angular.copy(data);
        image.id = (index + 1);
        image.name = 'image' + (index + 1);
        images.push(image);
      }
      return images;
    }

    describe('perform method', function() {

      beforeEach(function() {
        spyOn(deleteModalService, 'open').and.callThrough();
        service.initScope($scope, labelize);
      });

      function labelize(count) {
        return {
          title: ngettext('title', 'titles', count),
          message: ngettext('message', 'messages', count),
          submit: ngettext('submit', 'submits', count),
          success: ngettext('success', 'successs', count),
          error: ngettext('error', 'errors', count)
        };
      }

      ////////////

      it('should open the delete modal and show correct labels', testSingleLabels);
      it('should open the delete modal and show correct labels', testpluralLabels);
      it('should open the delete modal with correct entities', testEntities);
      it('should only delete images that are valid', testValids);
      it('should fail if this project is not owner', testOwner);
      it('should fail if images is protected', testProtected);
      it('should fail if status is deleted', testStatus);
      it('should pass in a function that deletes an image', testGlance);

      ////////////

      function testSingleLabels() {
        var images = generateImage(1);
        service.perform(images);
        $scope.$apply();

        var labels = deleteModalService.open.calls.argsFor(0)[2].labels;
        expect(deleteModalService.open).toHaveBeenCalled();
        for (var k in labels) { expect(labels[k].toLowerCase()).toContain('image'); }
      }

      function testpluralLabels() {
        var images = generateImage(2);
        service.perform(images);
        $scope.$apply();

        var labels = deleteModalService.open.calls.argsFor(0)[2].labels;
        expect(deleteModalService.open).toHaveBeenCalled();
        for (var k in labels) { expect(labels[k].toLowerCase()).toContain('images'); }
      }

      function testEntities() {
        var imageCount = 3;
        var images = generateImage(imageCount);
        service.perform(images);
        $scope.$apply();

        var entities = deleteModalService.open.calls.argsFor(0)[1];
        expect(deleteModalService.open).toHaveBeenCalled();
        expect(entities.length).toEqual(imageCount);
      }

      function testValids() {
        var imageCount = 2;
        var images = generateImage(imageCount);
        service.perform(images);
        $scope.$apply();

        var entities = deleteModalService.open.calls.argsFor(0)[1];
        expect(deleteModalService.open).toHaveBeenCalled();
        expect(entities.length).toBe(imageCount);
        expect(entities[0].name).toEqual('image1');
        expect(entities[1].name).toEqual('image2');
      }

      function testOwner() {
        var images = generateImage(1);
        deferred.reject();
        service.perform(images);
        $scope.$apply();

        expect(deleteModalService.open).not.toHaveBeenCalled();
      }

      function testProtected() {
        var images = generateImage(1);
        images[0].protected = true;
        service.perform(images);
        $scope.$apply();

        expect(deleteModalService.open).not.toHaveBeenCalled();
      }

      function testStatus() {
        var images = generateImage(1);
        images[0].status = 'deleted';
        service.perform(images);
        $scope.$apply();

        expect(deleteModalService.open).not.toHaveBeenCalled();
      }

      function testGlance() {
        spyOn(glanceAPI, 'deleteImage');
        var imageCount = 1;
        var images = generateImage(imageCount);
        var image = images[0];
        service.perform(images);
        $scope.$apply();

        var contextArg = deleteModalService.open.calls.argsFor(0)[2];
        var deleteFunction = contextArg.deleteEntity;
        deleteFunction(image.id);
        expect(glanceAPI.deleteImage).toHaveBeenCalledWith(image.id, true);
      }

    }); // end of delete modal

    describe('allow method', function() {

      var resolver = {
        success: function() {},
        error: function() {}
      };

      beforeEach(function() {
        spyOn(resolver, 'success');
        spyOn(resolver, 'error');
        service.initScope($scope);
      });

      ////////////

      it('should use default policy if batch action', testBatch);
      it('allows delete if image can be deleted', testValid);
      it('disallows delete if image is protected', testProtected);
      it('disallows delete if image is not owned by user', testOwner);
      it('disallows delete if image status is deleted', testStatus);

      ////////////

      function testBatch() {
        service.allowed();
        $scope.$apply();
        expect(policyAPI.ifAllowed).toHaveBeenCalled();
        expect(resolver.success).not.toHaveBeenCalled();
        expect(resolver.error).not.toHaveBeenCalled();
      }

      function testValid() {
        var image = generateImage(1)[0];
        service.allowed(image).then(resolver.success, resolver.error);
        $scope.$apply();
        expect(resolver.success).toHaveBeenCalled();
      }

      function testProtected() {
        var image = generateImage(1)[0];
        image.protected = true;
        service.allowed(image).then(resolver.success, resolver.error);
        $scope.$apply();
        expect(resolver.error).toHaveBeenCalled();
      }

      function testOwner() {
        var image = generateImage(1)[0];
        deferred.reject();
        service.allowed(image).then(resolver.success, resolver.error);
        $scope.$apply();
        expect(resolver.error).toHaveBeenCalled();
      }

      function testStatus() {
        var image = generateImage(1)[0];
        image.status = 'deleted';
        service.allowed(image).then(resolver.success, resolver.error);
        $scope.$apply();
        expect(resolver.error).toHaveBeenCalled();
      }

    }); // end of allowed

  }); // end of delete-image

})();
