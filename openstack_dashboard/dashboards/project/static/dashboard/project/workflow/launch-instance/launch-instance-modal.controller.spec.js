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

  describe('LaunchInstanceModalController tests', function() {
    var ctrl, modalService;

    beforeEach(module('horizon.dashboard.project'));

    beforeEach(module(function($provide) {
      modalService = {
        open: function() { }
      };

      $provide.value(
        'horizon.dashboard.project.workflow.launch-instance.modal.service',
        modalService
      );
    }));

    beforeEach(inject(function($controller) {
      ctrl = $controller('LaunchInstanceModalController');
    }));

    it('defines the controller', function() {
      expect(ctrl).toBeDefined();
    });

    it('defines openLaunchInstanceWizard', function() {
      expect(ctrl.openLaunchInstanceWizard).toBeDefined();
    });

    describe('openLaunchInstanceWizard function tests', function() {
      var func, launchContext;

      beforeEach(function() {
        func = ctrl.openLaunchInstanceWizard;
        launchContext = {};
      });

      it('calls modal.service.open', function() {
        spyOn(modalService, 'open').and.callThrough();
        func(launchContext);
        expect(modalService.open).toHaveBeenCalled();
      });

      it('calls modalService.open with expected values', function() {
        spyOn(modalService, 'open').and.callThrough();
        launchContext = { info: 'information' };
        func(launchContext);

        var args = modalService.open.calls.argsFor(0)[0];
        expect(args).toEqual(launchContext);
      });

    });
  });

})();
