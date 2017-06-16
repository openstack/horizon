/*
 *    (c) Copyright 2015 Hewlett-Packard Development Company, L.P.
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *    http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

(function() {
  'use strict';

  describe('Launch Instance Create Key Pair Controller ', function() {

    var ctrl, mockCreationSuccess, mockKeypair;
    var mockExistingKeypairs = ['anExistingKeypair'];
    var modalInstanceMock = {
      close: angular.noop,
      dismiss: angular.noop
    };

    var toastServiceMock = {add: angular.noop};

    var createKeypairServiceMock = {
      createAndDownloadKeypair: function() {
        return createKeypairPromise;
      },
      getRegenerateKeypairUrl: angular.noop
    };
    var createKeypairPromise = {
      then: function(resolve, reject) {
        if (mockCreationSuccess) {
          resolve(mockKeypair);
        } else {
          reject();
        }
      }
    };

    beforeEach(module('horizon.dashboard.project'));

    beforeEach(module(function ($provide) {
      $provide.value('$uibModalInstance', modalInstanceMock);
      $provide.value('horizon.framework.widgets.toast.service', toastServiceMock);
      $provide.value('existingKeypairs', mockExistingKeypairs);
      $provide.value(
        'horizon.app.core.openstack-service-api.nova',
        createKeypairServiceMock
      );
      $provide.value(
        'horizon.app.core.openstack-service-api.keypair-download-service',
        createKeypairServiceMock
      );
    }));

    beforeEach(
      inject(
        function($controller, $rootScope) {
          ctrl = $controller('LaunchInstanceCreateKeyPairController', {
            $scope: $rootScope
          });
        }
      )
    );

    it('should instantiate with default values', function() {
      expect(ctrl.keypair).toEqual('');
      var msg = 'Keypair already exists or name contains bad characters.';
      expect(ctrl.keypairExistsError).toEqual(msg);
    });

    it('should close the modal and return the created keypair', function() {
      spyOn(modalInstanceMock, 'close');

      ctrl.createdKeypair = {name: 'newKeypair'};
      ctrl.submit();

      expect(modalInstanceMock.close).toHaveBeenCalledWith({
        name: "newKeypair"
      });
    });

    it('defines a submit function', function() {
      expect(ctrl.submit).toBeDefined();
    });

    it('should define a cancel function', function() {
      expect(ctrl.cancel).toBeDefined();
    });

    it('should define a doesKeypairExist function', function() {
      expect(ctrl.doesKeypairExist).toBeDefined();
    });

    it('cancel dimisses the modal', function() {
      spyOn(modalInstanceMock, 'dismiss');
      ctrl.cancel();
      expect(modalInstanceMock.dismiss).toHaveBeenCalled();
    });

    it('should check to see if the keypair already exists', function() {
      ctrl.keypair = 'aUniqueKeypair';
      expect(ctrl.doesKeypairExist()).toBe(false);

      ctrl.keypair = 'anExistingKeypair';
      expect(ctrl.doesKeypairExist()).toBe(true);
    });

  });
})();
