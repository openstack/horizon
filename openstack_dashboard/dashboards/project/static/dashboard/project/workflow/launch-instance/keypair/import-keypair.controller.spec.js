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

  describe('Launch Instance Import Key Pair Controller', function() {

    var novaAPI, ctrl, toastService, $q, $rootScope;
    var model = { name: 'newKeypair', public_key: '' };
    var modalInstanceMock = {
      close: angular.noop,
      dismiss: angular.noop
    };

    beforeEach(module('horizon.app.core.openstack-service-api'));
    beforeEach(module('horizon.dashboard.project'));
    beforeEach(module('horizon.framework'));

    beforeEach(inject(function($injector, $controller, _$q_, _$rootScope_) {
      novaAPI = $injector.get('horizon.app.core.openstack-service-api.nova');
      ctrl = $controller('LaunchInstanceImportKeyPairController', {
        $modalInstance: modalInstanceMock
      });
      toastService = $injector.get('horizon.framework.widgets.toast.service');
      $q = _$q_;
      $rootScope = _$rootScope_;
    }));

    it('defines a model with an empty name and public key', function() {
      expect(ctrl.model).toBeDefined();
      expect(ctrl.model.name).toBe('');
      expect(ctrl.model.public_key).toBe('');
    });

    it('defines a submit function', function() {
      expect(ctrl.submit).toBeDefined();
    });

    it('submit successfully imports keypair and closes modal', function() {
      var deferredSuccess = $q.defer();
      spyOn(novaAPI, 'createKeypair').and.returnValue(deferredSuccess.promise);
      spyOn(modalInstanceMock, 'close');
      spyOn(toastService, 'add').and.callThrough();

      ctrl.submit();

      deferredSuccess.resolve(model);
      $rootScope.$apply();

      expect(novaAPI.createKeypair).toHaveBeenCalled();
      expect(modalInstanceMock.close).toHaveBeenCalled();
      expect(toastService.add).toHaveBeenCalledWith(
        'success',
        'Successfully imported key pair newKeypair.');
    });

    it('defines a cancel function', function() {
      expect(ctrl.cancel).toBeDefined();
    });

    it('cancel dismisses the modal', function() {
      spyOn(modalInstanceMock, 'dismiss').and.callThrough();
      ctrl.cancel();
      expect(modalInstanceMock.dismiss).toHaveBeenCalled();
    });

  });
})();
