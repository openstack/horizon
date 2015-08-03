/*
 *    (c) Copyright 2015 Hewlett-Packard Development Company, L.P.
 *
 * Licensed under the Apache License, Version 2.0 (the 'License');
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *    http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an 'AS IS' BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */
(function () {
  'use strict';

  describe('LaunchInstanceWizardController tests', function() {
    var ctrl;
    var model = {
      createInstance: function() {
        return 'created';
      },
      initialize: angular.noop
    };
    var scope = {};

    beforeEach(module('horizon.dashboard.project'));
    beforeEach(module(function ($provide) {
      $provide.value('serviceCatalog', {});
      $provide.value('launchInstanceModel', model);
      $provide.value('horizon.dashboard.project.workflow.launch-instance.workflow',
        { thing: true });
    }));
    beforeEach(inject(function ($controller) {
      spyOn(model, 'initialize');
      ctrl = $controller('LaunchInstanceWizardController', {$scope: scope});
    }));

    it('defines the controller', function() {
      expect(ctrl).toBeDefined();
    });

    it('calls initialize on the given model', function() {
      expect(scope.model.initialize).toHaveBeenCalled();
    });

    it('sets scope.workflow to the given workflow', function() {
      expect(scope.workflow).toEqual({ thing: true });
    });

    it('defines scope.submit', function() {
      expect(scope.submit).toBeDefined();
      expect(scope.submit()).toBe('created');
    });
  });

})();
