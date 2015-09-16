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

      beforeEach(module(function ($provide) {
        $provide.value('$modal', {});
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

    });

    describe('LaunchInstanceCreateKeyPairController', function() {
      var ctrl;

      beforeEach(module(function ($provide) {
        $provide.value('$modalInstance', {});
        $provide.value('horizon.app.core.openstack-service-api.nova', {});
        $provide.value('horizon.framework.widgets.toast.service', {});
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

      it('defines a cancel function', function() {
        expect(ctrl.cancel).toBeDefined();
      });
    });

    describe('LaunchInstanceNewKeyPairController', function() {
      var ctrl;

      beforeEach(module(function ($provide) {
        $provide.value('$modalInstance', {});
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
    });

    describe('LaunchInstanceImportKeyPairController', function() {
      var ctrl;

      beforeEach(module(function ($provide) {
        $provide.value('$modalInstance', {});
        $provide.value('horizon.app.core.openstack-service-api.nova', {});
        $provide.value('horizon.framework.widgets.toast.service', {});
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

      it('defines a cancel function', function() {
        expect(ctrl.cancel).toBeDefined();
      });
    });
  });

})();

