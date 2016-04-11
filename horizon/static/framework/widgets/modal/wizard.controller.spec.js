/**
 * Copyright 2015 IBM Corp.
 *
 * Licensed under the Apache License, Version 2.0 (the "License"); you may
 * not use this file except in compliance with the License. You may obtain
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

  var wizardCtrl = 'WizardModalController';
  describe(wizardCtrl, function() {

    var modalCalls = [ 'close', 'dismiss' ];
    var modalInstance = jasmine.createSpyObj('$modalInstance', modalCalls);

    var scope;

    //////////

    beforeEach(module('horizon.framework.widgets.modal'));
    beforeEach(inject(function($controller, $rootScope) {
      scope = $rootScope.$new();
      $controller(wizardCtrl, {
        $modalInstance: modalInstance,
        $scope: scope,
        workflow: { steps: 'somestep' },
        submit: { api: 'someapi' }
      });
    }));

    //////////

    it('should inject and assign workflow and submit', injectAssign);
    it('should forward call to modalInstance on close', closeModal);
    it('should forward call to modalInstance on cancel', cancelModal);

    //////////

    function injectAssign() {
      expect(scope.workflow.steps).toEqual('somestep');
      expect(scope.submit.api).toEqual('someapi');
    }

    function closeModal() {
      scope.close();
      expect(modalInstance.close).toHaveBeenCalled();
    }

    function cancelModal() {
      scope.cancel();
      expect(modalInstance.dismiss).toHaveBeenCalledWith('cancel');
    }

  });

})();
