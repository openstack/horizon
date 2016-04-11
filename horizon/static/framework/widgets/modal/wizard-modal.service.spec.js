/**
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 * http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

(function() {
  "use strict";

  describe('horizon.framework.widgets.wizard-modal.service', function() {
    var service, modal, $scope;

    beforeEach(module('horizon.framework'));
    beforeEach(module(function($provide) {
      modal = {
        open: function() {}
      };
      $provide.value('$modal', modal);
    }));

    beforeEach(inject(function($injector, _$rootScope_) {
      $scope = _$rootScope_.$new();
      service = $injector.get('horizon.framework.widgets.modal.wizard-modal.service');
    }));

    it('defines the service', function() {
      expect(service).toBeDefined();
    });

    it('does not open the modal if called with no parameters', function() {
      spyOn(modal, 'open').and.callThrough();
      service.modal();
      expect(modal.open).not.toHaveBeenCalled();
    });

    it('should open the modal if called with required parameters', function() {
      spyOn(modal, 'open').and.callThrough();
      service.modal({scope: $scope, workflow: {}, submit: {}});
      expect(modal.open).toHaveBeenCalled();
    });

    it('should open the modal with correct parameters', function() {
      spyOn(modal, 'open').and.callThrough();
      var workflow = {id: 'w'};
      var submit = {id: 's'};
      service.modal({scope: $scope, workflow: workflow, submit: submit});
      expect(modal.open).toHaveBeenCalled();
      var modalOpenArgs = modal.open.calls.argsFor(0)[0];
      expect(modalOpenArgs.controller).toEqual('WizardModalController as modalCtrl');
      expect(modalOpenArgs.scope).toEqual($scope);
      expect(modalOpenArgs.resolve.workflow()).toEqual(workflow);
      expect(modalOpenArgs.resolve.submit()).toEqual(submit);
    });
  });

})();
