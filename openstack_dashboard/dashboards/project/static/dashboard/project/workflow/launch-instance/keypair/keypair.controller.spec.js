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
      var ctrl, q, settings;
      var $uibModal = { open: angular.noop };
      var toastServiceMock = {add: angular.noop};

      beforeEach(module('horizon.dashboard.project'));

      beforeEach(function() {
        settings = {
          OPENSTACK_HYPERVISOR_FEATURES: {
            requires_keypair: false
          }
        };
      });

      beforeEach(module(function ($provide) {
        $provide.value('$uibModal', $uibModal);
        $provide.value('horizon.framework.widgets.toast.service', toastServiceMock);
        $provide.value('horizon.app.core.openstack-service-api.settings', {
          getSetting: function(setting) {
            setting = setting.split('.');
            var deferred = q.defer();
            deferred.resolve(settings[setting[0]][setting[1]]);
            return deferred.promise;
          }
        });
      }));

      beforeEach(inject(function($controller, $q) {
        q = $q;
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
        expect(Object.keys(ctrl.tableData).length).toBe(2);
        expect(ctrl.tableData.available).toEqual([{name: 'key1'}, {name: 'key2'}]);
        expect(ctrl.tableData.allocated).toEqual(['key1']);
      });

      it('defines table details template', function() {
        expect(ctrl.availableTableConfig.detailsTemplateUrl).toBeDefined();
      });

      it('defines a custom no items message for allocated table', function() {
        expect(ctrl.allocatedTableConfig.noItemsMessage).toBeDefined();
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
        spyOn($uibModal, 'open').and.returnValue({result: {then: angular.noop}});
        ctrl.createKeyPair();
        expect($uibModal.open).toHaveBeenCalled();
      });

      it('should pass the create keypair submodal the existing keypairs', function() {
        spyOn($uibModal, 'open').and.returnValue({
          result: {then: angular.noop}
        });
        ctrl.createKeyPair();

        var modalParameters = $uibModal.open.calls.mostRecent().args[0];
        expect(modalParameters.resolve.existingKeypairs()).toEqual(['key1','key2']);
      });

      function getCreateKeypairModalCallback() {
        var result = {result: {then: angular.noop}};
        spyOn(result.result, 'then');
        spyOn($uibModal, 'open').and.returnValue(result);

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
        spyOn($uibModal, 'open').and.returnValue({result: {then: angular.noop}});
        ctrl.importKeyPair();
        expect($uibModal.open).toHaveBeenCalled();
      });

      it('importKeyPairCallback is called', function() {
        var result = {result: {then: angular.noop}};
        spyOn(result.result, 'then');
        spyOn($uibModal, 'open').and.returnValue(result);
        ctrl.importKeyPair();
        var importKeypairModalcallback = result.result.then.calls.argsFor(0)[0];

        var callbackInput = {name: "June"};
        $uibModal.open.calls.reset();
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

      it('defines isKeypairRequired', function() {
        expect(ctrl.isKeypairRequired).toBeDefined();
        expect(ctrl.isKeypairRequired).toBe(0);
      });

      it('sets isKeypairRequired properly', function() {
        expect(ctrl.isKeypairRequired).toBeDefined();
        ctrl.setKeypairRequired(true);
        expect(ctrl.isKeypairRequired).toBe(1);
        ctrl.setKeypairRequired(false);
        expect(ctrl.isKeypairRequired).toBe(0);
      });
    });

  });

})();

