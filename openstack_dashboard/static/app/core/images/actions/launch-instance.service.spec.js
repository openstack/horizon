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

  describe('horizon.app.core.images.actions.launch-instance.service', function() {

    var launchInstanceModalMock = {
      open: function () {}
    };

    var service, $scope;

    ///////////////////////
    beforeEach(module('horizon.framework'));
    beforeEach(module('horizon.app.core'));
    beforeEach(module('horizon.dashboard.project.workflow.launch-instance', function($provide) {
      $provide.value(
        'horizon.dashboard.project.workflow.launch-instance.modal.service', launchInstanceModalMock
      );
    }));

    beforeEach(inject(function($injector, _$rootScope_) {
      service = $injector.get('horizon.app.core.images.actions.launch-instance.service');
      $scope = _$rootScope_.$new();
    }));

    it('should open the modal with correct message', function() {
      spyOn(launchInstanceModalMock, 'open').and.callThrough();

      service.perform({id: '1', name: 'image1'});

      expect(launchInstanceModalMock.open).toHaveBeenCalled();
      expect(launchInstanceModalMock.open.calls.argsFor(0)).toEqual([{
        imageId: '1'
      }]);
    });

    describe('launch instance', function() {
      it('should allow launch instance if image can be launched', function() {
        var image = {container_format: 'ami', status: 'active'};
        permissionShouldPass(service.allowed(image));
        $scope.$apply();
      });

      it('should not allow launch instance if image is not bootable', function() {
        var image = {container_format: 'ari', status: 'active'};
        permissionShouldFail(service.allowed(image));
        $scope.$apply();
      });

      it('should not allow launch instance if image status is not active', function() {
        var image = {container_format: 'ari', status: 'not_active'};
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
