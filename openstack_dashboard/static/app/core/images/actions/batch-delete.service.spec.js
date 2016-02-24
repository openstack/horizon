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

  describe('horizon.app.core.images.actions.batch-delete.service', function() {

    var deleteImageService = {
      initScope: function() {},
      perform: function () {}
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

    var service, $scope;

    ///////////////////////

    beforeEach(module('horizon.framework'));
    beforeEach(module('horizon.app.core'));
    beforeEach(module('horizon.app.core.openstack-service-api', function($provide) {
      $provide.value('horizon.app.core.openstack-service-api.policy', policyAPI);
    }));
    beforeEach(module('horizon.app.core.images', function($provide) {
      $provide.value('horizon.app.core.images.actions.delete-image.service', deleteImageService);
    }));
    beforeEach(inject(function($injector, _$rootScope_) {
      $scope = _$rootScope_.$new();
      service = $injector.get('horizon.app.core.images.actions.batch-delete.service');
    }));

    it('should init the deleteImageService', function() {
      spyOn(deleteImageService, 'initScope').and.callThrough();

      service.initScope($scope);

      expect(deleteImageService.initScope).toHaveBeenCalled();
    });

    it('should check the policy if the user is allowed to delete images', function() {
      spyOn(policyAPI, 'ifAllowed').and.callThrough();
      var allowed = service.allowed();
      expect(allowed).toBeTruthy();
      expect(policyAPI.ifAllowed).toHaveBeenCalledWith({ rules: [['image', 'delete_image']] });
    });

    it('pass the image to the deleteImageService', function() {

      spyOn(deleteImageService, 'perform').and.callThrough();
      var selected = [
        {id: '1', name: 'image1'},
        {id: '2', name: 'image2'}
      ];

      service.perform(selected);
      expect(deleteImageService.perform).toHaveBeenCalledWith(selected);
    });

  });

})();
