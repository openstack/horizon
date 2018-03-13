/*
 * Copyright 2016 IBM Corp.
 *
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
(function () {
  'use strict';

  describe('Workflow Decorator', function () {
    var decoratorService, catalogService, policyService, settingsService, $scope, deferred,
      novaExtensionsService;
    var steps = [
      { id: '1' },
      { id: '2', requiredServiceTypes: ['foo-service'] },
      { id: '3', policy: 'foo-policy' },
      { id: '4', setting: 'STEPS.step_4_enabled' },
      { id: '5', novaExtension: 'foo-novaExtension'}
    ];
    var spec = { steps: steps };

    beforeEach(module('horizon.app.core'));
    beforeEach(module('horizon.framework.util'));
    beforeEach(module('horizon.framework.conf'));
    beforeEach(module('horizon.framework.widgets.toast'));

    beforeEach(inject(function($injector) {
      $scope = $injector.get('$rootScope').$new();
      deferred = $injector.get('$q').defer();
      decoratorService = $injector.get('horizon.app.core.workflow.decorator');
      catalogService = $injector.get('horizon.app.core.openstack-service-api.serviceCatalog');
      policyService = $injector.get('horizon.app.core.openstack-service-api.policy');
      settingsService = $injector.get('horizon.app.core.openstack-service-api.settings');
      novaExtensionsService = $injector
                                .get('horizon.app.core.openstack-service-api.novaExtensions');
      spyOn(catalogService, 'ifTypeEnabled').and.returnValue(deferred.promise);
      spyOn(policyService, 'ifAllowed').and.returnValue(deferred.promise);
      spyOn(settingsService, 'ifEnabled').and.returnValue(deferred.promise);
      spyOn(novaExtensionsService, 'ifNameEnabled').and.returnValue(deferred.promise);
    }));

    it('is a function', function() {
      expect(angular.isFunction(decoratorService)).toBe(true);
    });

    it('checks each step for required services, policies, and settings', function() {
      decoratorService(spec);
      expect(steps[0].checkReadiness).toBeUndefined();
      expect(steps[1].checkReadiness).toBeDefined();
      expect(steps[2].checkReadiness).toBeDefined();
      expect(catalogService.ifTypeEnabled.calls.count()).toBe(1);
      expect(catalogService.ifTypeEnabled).toHaveBeenCalledWith('foo-service');
      expect(policyService.ifAllowed.calls.count()).toBe(1);
      expect(policyService.ifAllowed).toHaveBeenCalledWith('foo-policy');
      expect(settingsService.ifEnabled.calls.count()).toBe(1);
      expect(settingsService.ifEnabled).toHaveBeenCalledWith('STEPS.step_4_enabled', true, true);
      expect(novaExtensionsService.ifNameEnabled.calls.count()).toBe(1);
      expect(novaExtensionsService.ifNameEnabled).toHaveBeenCalledWith('foo-novaExtension');
    });

    it('step checkReadiness function returns true when promise is resolved', function() {
      decoratorService(spec);
      var readinessResult;
      deferred.resolve('foo');
      steps[1].checkReadiness().then(function(result) {
        readinessResult = result;
      });
      $scope.$apply();
      expect(readinessResult).toEqual(true);
    });

    it('step checkReadiness function returns false when promise is rejected', function() {
      decoratorService(spec);
      var readinessResult;
      deferred.reject();
      steps[1].checkReadiness().then(function(result) {
        readinessResult = result;
      });
      $scope.$apply();
      expect(readinessResult).toEqual(false);
    });

  });

})();
