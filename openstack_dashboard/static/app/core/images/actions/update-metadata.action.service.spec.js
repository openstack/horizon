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

  describe('horizon.app.core.images.actions.update-metadata.service', function() {
    var service, $scope;

    var metadataModalMock = {
      open: function () {}
    };

    var policyAPI = {
      ifAllowed: function() {
        return {
          success: function(callback) {
            callback({allowed: false});
          }
        };
      }
    };

    ///////////////////////

    beforeEach(module('horizon.framework'));
    beforeEach(module('horizon.app.core'));
    beforeEach(module('horizon.app.core.metadata.modal', function($provide) {
      $provide.value('horizon.app.core.metadata.modal.service', metadataModalMock);
    }));

    beforeEach(inject(function($injector, _$rootScope_) {
      $scope = _$rootScope_.$new();
      service = $injector.get('horizon.app.core.images.actions.update-metadata.service');
    }));

    it('should open the modal with correct message', function() {
      var fakeModalService = {
        result: {
          then: function (callback) {
            callback();
          }
        }
      };

      spyOn(metadataModalMock, 'open').and.returnValue(fakeModalService);

      service.perform({id: '1', name: 'image1'});

      expect(metadataModalMock.open).toHaveBeenCalled();
      expect(metadataModalMock.open.calls.argsFor(0)).toEqual(['image', '1']);
    });

    describe('Update Metadata', function() {
      function policyIfAllowed() {
        return {
          then: function(callback) {
            callback({allowed: true});
          }
        };
      }

      beforeEach(inject(function ($injector) {
        policyAPI = $injector.get('horizon.app.core.openstack-service-api.policy');
        spyOn(policyAPI, 'ifAllowed').and.callFake(policyIfAllowed);
      }));

      it('should allow Update Metadata if image can be deleted', function() {
        var image = {owner: 'project', status: 'active'};
        permissionShouldPass(service.allowed(image));
        $scope.$apply();
      });

      it('should not allow Update Metadata if image status is not active', function() {
        var image = {owner: 'project', status: 'not_active'};
        permissionShouldFail(service.allowed(image));
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
