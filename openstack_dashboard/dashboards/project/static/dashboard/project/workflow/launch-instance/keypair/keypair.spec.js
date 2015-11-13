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

    describe('LaunchInstanceKeypairController', function() {
      var ctrl;
      var $modal = { open: angular.noop };

      beforeEach(module(function ($provide) {
        $provide.value('$modal', $modal);
      }));

      beforeEach(module('horizon.dashboard.project'));

      beforeEach(inject(function($controller) {
        var model = {
          newInstanceSpec: {
            key_pair: ['key1']
          },
          keypairs: ['key1', 'key2']
        };

        ctrl = $controller('LaunchInstanceKeypairController',
                          { launchInstanceModel: model });
      }));

      it('contains its table labels', function() {
        expect(ctrl.tableData).toBeDefined();
        expect(Object.keys(ctrl.tableData).length).toBeGreaterThan(0);
      });

      it('sets table data to appropriate scoped items', function() {
        expect(ctrl.tableData).toBeDefined();
        expect(Object.keys(ctrl.tableData).length).toBe(4);
        expect(ctrl.tableData.available).toEqual(['key1', 'key2']);
        expect(ctrl.tableData.allocated).toEqual(['key1']);
        expect(ctrl.tableData.displayedAvailable).toEqual([]);
        expect(ctrl.tableData.displayedAllocated).toEqual([]);
      });

      it('defines table details template', function() {
        expect(ctrl.tableDetails).toBeDefined();
      });

      it('allows allocation of only one', function() {
        expect(ctrl.tableLimits).toBeDefined();
        expect(Object.keys(ctrl.tableLimits).length).toBe(1);
        expect(ctrl.tableLimits.maxAllocation).toBe(1);
      });

      it('allocateNewKeypair does nothing if some allocated', function() {
        ctrl.tableData.allocated = ['something'];
        spyOn(ctrl.tableData.allocated, 'push');
        ctrl.allocateNewKeyPair('do not use');
        expect(ctrl.tableData.allocated.length).toBe(1);
        expect(ctrl.tableData.allocated.push).not.toHaveBeenCalled();
      });

      it('allocateNewKeypair adds keypair if none allocated', function() {
        ctrl.tableData.allocated = [];
        ctrl.allocateNewKeyPair('new');
        expect(ctrl.tableData.allocated).toEqual(['new']);
      });

      it('createKeyPair opens a modal', function() {
        spyOn($modal, 'open').and.returnValue({result: {then: angular.noop}});
        ctrl.createKeyPair();
        expect($modal.open).toHaveBeenCalled();
      });

      it('createKeyPairCallback is called', function() {
        var result = {result: {then: angular.noop}};
        spyOn(result.result, 'then');
        spyOn($modal, 'open').and.returnValue(result);
        ctrl.createKeyPair();
        var callback = result.result.then.calls.argsFor(0)[0];

        var callbackInput = {name: "June"};
        $modal.open.calls.reset();
        callback(callbackInput);
        expect($modal.open).toHaveBeenCalled();
        expect(callbackInput.id).toBe("June");
      });

      it('importKeyPair opens a modal', function() {
        spyOn($modal, 'open').and.returnValue({result: {then: angular.noop}});
        ctrl.importKeyPair();
        expect($modal.open).toHaveBeenCalled();
      });

      it('importKeyPairCallback is called', function() {
        var result = {result: {then: angular.noop}};
        spyOn(result.result, 'then');
        spyOn($modal, 'open').and.returnValue(result);
        ctrl.importKeyPair();
        var callback = result.result.then.calls.argsFor(0)[0];

        var callbackInput = {name: "June"};
        $modal.open.calls.reset();
        callback(callbackInput);
        expect(callbackInput.id).toBe("June");
      });
    });

    describe('LaunchInstanceCreateKeyPairController', function() {
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
        ctrl = $controller('LaunchInstanceCreateKeyPairController');
      }));

      it('defines a model with a empty name', function() {
        expect(ctrl.model).toBeDefined();
        expect(ctrl.model.name).toBe('');
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

      it('cancel dismisses the modal', function() {
        spyOn(nova, 'createKeypair').and.returnValue({success: angular.noop});
        spyOn($modalInstance, 'dismiss');
        ctrl.cancel();
        expect($modalInstance.dismiss).toHaveBeenCalledWith();
      });
    });

    describe('LaunchInstanceNewKeyPairController', function() {
      var ctrl;
      var $modalInstance = {close: angular.noop, dismiss: angular.noop};

      beforeEach(module(function ($provide) {
        $provide.value('$modalInstance', $modalInstance);
      }));

      beforeEach(module('horizon.dashboard.project'));

      beforeEach(inject(function($controller) {
        ctrl = $controller('LaunchInstanceNewKeyPairController', { keypair: {} });
      }));

      it('defines an empty keypair', function() {
        expect(ctrl.keypair).toBeDefined();
      });

      it('defines an OK function', function() {
        expect(ctrl.ok).toBeDefined();
      });

      it('ok dismisses the window', function() {
        spyOn($modalInstance, 'dismiss');
        ctrl.ok();
        expect($modalInstance.dismiss).toHaveBeenCalledWith();
      });
    });

    describe('LaunchInstanceImportKeyPairController', function() {
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

