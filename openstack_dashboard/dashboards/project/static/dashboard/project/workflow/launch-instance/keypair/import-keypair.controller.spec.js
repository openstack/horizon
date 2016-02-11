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

  describe('Launch Instance Keypair Step', function() {

    describe('Import Key Pair Controller', function() {
      var ctrl;
      var nova = { createKeypair: angular.noop };
      var $modalInstance = {close: angular.noop, dismiss: angular.noop};

      beforeEach(module(function ($provide) {
        $provide.value('$modalInstance', $modalInstance);
        $provide.value('horizon.app.core.openstack-service-api.nova', nova);
        $provide.value('horizon.framework.widgets.toast.service', {add: angular.noop});
      }));

      beforeEach(module('horizon.dashboard.project'));

      beforeEach(inject(function($controller) {
        ctrl = $controller('LaunchInstanceImportKeyPairController');
      }));

      it('defines a model with a empty name and public key', function() {
        expect(ctrl.model).toBeDefined();
        expect(ctrl.model.name).toBe('');
        expect(ctrl.model.public_key).toBe('');
      });

      it('defines a submit function', function() {
        expect(ctrl.submit).toBeDefined();
      });

      it('submit calls nova with the proper arguments', function() {
        spyOn(nova, 'createKeypair').and.returnValue({success: angular.noop});
        ctrl.submit();
        expect(nova.createKeypair).toHaveBeenCalledWith(ctrl.model);
      });

      it('successful submit calls the successCallback', function() {
        var successFunc = {success: angular.noop};
        spyOn(nova, 'createKeypair').and.returnValue(successFunc);
        spyOn(successFunc, 'success');
        ctrl.submit();
        var successCallback = successFunc.success.calls.argsFor(0)[0];
        var data = {};
        successCallback(data);
      });

      it('defines a cancel function', function() {
        expect(ctrl.cancel).toBeDefined();
      });

      it('cancel dimisses the modal', function() {
        spyOn(nova, 'createKeypair').and.returnValue({success: angular.noop});
        spyOn($modalInstance, 'dismiss');
        ctrl.cancel();
        expect($modalInstance.dismiss).toHaveBeenCalledWith();
      });
    });
  });

})();
