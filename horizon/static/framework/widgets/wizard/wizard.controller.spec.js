/*
 *    (c) Copyright 2017 SUSE Linux
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

  describe("WizardController", function() {
    var ctrl, scope, wizardLabels, wizardEvents, frameworkEvents, rootScope;
    beforeEach(module('horizon.framework'));
    beforeEach(inject(function($controller, $rootScope, $injector, $q) {
      scope = $rootScope.$new();
      rootScope = $rootScope;
      wizardLabels = $injector.get('horizon.framework.widgets.wizard.labels');
      wizardEvents = $injector.get('horizon.framework.widgets.wizard.events');
      frameworkEvents = $injector.get('horizon.framework.events');
      ctrl = $controller('WizardController', {
        $scope: scope,
        $q: $q,
        wizardLabels: wizardLabels,
        wizardEvents: wizardEvents,
        frameworkEvents: frameworkEvents
      });
      scope.$apply();
    }));

    it('is defined', function() {
      expect(ctrl).toBeDefined();
    });

    it('viewModel is defined', function() {
      expect(scope.viewModel).toBeDefined();
    });

    it('call switchTo', function() {
      spyOn(ctrl, 'toggleHelpBtn');
      spyOn(scope, '$broadcast');
      scope.switchTo(1);
      scope.$apply();
      expect(ctrl.toggleHelpBtn).toHaveBeenCalled();
      expect(scope.currentIndex).toBe(1);
      expect(scope.openHelp).toBe(false);
      expect(scope.$broadcast).toHaveBeenCalled();
    });

    it('call showError', function() {
      spyOn(scope, 'showError').and.callThrough();
      scope.showError('in valid');
      scope.$apply();
      expect(scope.viewModel.hasError).toBe(true);
      expect(scope.viewModel.errorMessage).toBe('in valid');
    });

    it('call onInitSuccess with auth_error event', function() {
      rootScope.$broadcast(frameworkEvents.AUTH_ERROR, 'auth_error');
      ctrl.onInitSuccess();
      scope.$apply();
      expect(scope.viewModel.hasError).toBe(true);
    });

    it('call onInitSuccess without auth_error event', function() {
      spyOn(scope, '$broadcast');
      ctrl.onInitSuccess();
      scope.$apply();
      expect(scope.viewModel.hasError).toBe(false);
      expect(scope.$broadcast).toHaveBeenCalledWith(wizardEvents.ON_INIT_SUCCESS);
    });

    it('call onInitError with auth_error event', function() {
      rootScope.$broadcast(frameworkEvents.AUTH_ERROR, 'auth_error');
      ctrl.onInitError();
      scope.$apply();
      expect(scope.viewModel.hasError).toBe(true);
    });

    it('call onInitError without logout event', function() {
      spyOn(scope, '$broadcast');
      ctrl.onInitError();
      scope.$apply();
      expect(scope.viewModel.hasError).toBe(false);
      expect(scope.$broadcast).toHaveBeenCalledWith(wizardEvents.ON_INIT_ERROR);
    });
  });

})();
