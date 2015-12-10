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
      var toastServiceMock = {add: angular.noop};

      beforeEach(module('horizon.dashboard.project'));

      beforeEach(module(function ($provide) {
        $provide.value('$modal', $modal);
        $provide.value('horizon.framework.widgets.toast.service', toastServiceMock);
      }));

      beforeEach(inject(function($controller) {
        var model = {
          newInstanceSpec: {
            key_pair: ['key1']
          },
          keypairs: [{name: 'key1'}, {name: 'key2'}]
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
        expect(ctrl.tableData.available).toEqual([{name: 'key1'}, {name: 'key2'}]);
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

      it('should pass the create keypair submodal the existing keypairs', function() {
        spyOn($modal, 'open').and.returnValue({
          result: {then: angular.noop}
        });
        ctrl.createKeyPair();

        var modalParameters = $modal.open.calls.mostRecent().args[0];
        expect(modalParameters.resolve.existingKeypairs()).toEqual(['key1','key2']);
      });

      function getCreateKeypairModalCallback() {
        var result = {result: {then: angular.noop}};
        spyOn(result.result, 'then');
        spyOn($modal, 'open').and.returnValue(result);

        ctrl.createKeyPair();

        return result.result.then.calls.argsFor(0)[0];
      }

      it('toasts success message if the key pair was added', function() {
        spyOn(toastServiceMock, 'add');

        var createKeypair = getCreateKeypairModalCallback();
        createKeypair({name: "newKeypair"});

        expect(toastServiceMock.add).toHaveBeenCalledWith(
            'success',
            'Created keypair: newKeypair'
        );
      });

      it('should display the regenerate url when the create keypair is successful', function() {
        var createKeypair = getCreateKeypairModalCallback();
        createKeypair({
          name: "newKeypair",
          regenerateUrl: "download url"
        });

        expect(ctrl.createdKeypair.name).toEqual("newKeypair");
        expect(ctrl.createdKeypair.regenerateUrl).toEqual('download url');
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
        var importKeypairModalcallback = result.result.then.calls.argsFor(0)[0];

        var callbackInput = {name: "June"};
        $modal.open.calls.reset();
        importKeypairModalcallback(callbackInput);
        expect(callbackInput.id).toBe("June");
      });

      it('should allocate a newly created keypair', function() {
        // the keypair is only allocated if none are currently allocated
        ctrl.tableData.allocated = [];

        var createKeypair = getCreateKeypairModalCallback();
        createKeypair({name: "newKeypair"});

        expect(ctrl.tableData.allocated[0].name).toEqual("newKeypair");
      });
    });

  });

})();

