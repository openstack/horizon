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

  describe('KeypairController', function() {
    var ctrl, keyPairCall, $timeout;
    var nova = {
      getKeypairs: function() {
        var kps = {data: {items: [{keypair: {name: 'one'}},{keypair: {name: 'two'}} ]}};
        keyPairCall.resolve(kps);
        return keyPairCall.promise;
      }
    };
    var spinner = {
      showModalSpinner: angular.noop
    };
    var config = {successUrl: '/some/where'};
    var $uibModal = {
      open: angular.noop
    };
    var $window = {location: {}};

    beforeEach(module('horizon.app.core.keypairs'));

    beforeEach(
      inject(
        function($controller, $rootScope, $q, _$timeout_) {
          $timeout = _$timeout_;
          ctrl = $controller('KeypairController', {
            'horizon.dashboard.project.workflow.launch-instance.basePath': '/here/',
            'horizon.app.core.openstack-service-api.nova': nova,
            'horizon.framework.widgets.modal-wait-spinner.service': spinner,
            '$uibModal': $uibModal,
            '$window': $window
          });

          keyPairCall = $q.defer();
          spyOn($uibModal, 'open').and.returnValue({result: $q.resolve({})});
        }
      )
    );

    describe('createKeyPair', function() {
      it('opens the modal', function() {
        ctrl.createKeyPair(config);
        $timeout.flush();
        expect($uibModal.open).toHaveBeenCalled();
      });

      it('provides a function to existingKeypairs that returns keypair names', function() {
        ctrl.createKeyPair(config);
        $timeout.flush();
        var func = $uibModal.open.calls.argsFor(0)[0].resolve.existingKeypairs;
        expect(func()).toEqual(['one','two']);
      });

      it('relocates to the config successUrl', function() {
        ctrl.createKeyPair(config);
        $timeout.flush();
        expect($window.location.href).toBe('/some/where');
      });
    });
  });

})();
