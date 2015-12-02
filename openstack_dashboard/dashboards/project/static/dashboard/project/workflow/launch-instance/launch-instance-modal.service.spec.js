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
    var service, modal, $window;

    beforeEach(module('horizon.dashboard.project'));
    beforeEach(module(function($provide) {
      modal = {
        open: function() {
          return {
            result: {
              then: angular.noop
            }
          };
        }
      };
      $window = { location: { href: '/' } };
      $provide.value('$modal', modal);
      $provide.value('$modalSpec', {});
      $provide.value('$window', $window);
    }));

    beforeEach(inject(function($injector) {
      service = $injector.get('horizon.dashboard.project.workflow.launch-instance.modal.service');
    }));

    describe('open function tests', function() {
      var func, launchContext;

      beforeEach(function() {
        func = service.open;
        launchContext = {};
      });

      it('calls modal.open', function() {
        spyOn(modal, 'open').and.returnValue({ result: { then: angular.noop } });
        func(launchContext);
        expect(modal.open).toHaveBeenCalled();
      });

      it('calls modal.open with expected values', function() {
        spyOn(modal, 'open').and.returnValue({ result: { then: angular.noop } });
        launchContext = { info: 'information' };
        func(launchContext);

        var resolve = modal.open.calls.argsFor(0)[0].resolve;
        expect(resolve).toBeDefined();
        expect(resolve.launchContext).toBeDefined();
        expect(resolve.launchContext()).toEqual({ info: 'information' });
      });

      it('sets up the correct success and failure paths', function() {
        var successFunc, errFunc;

        launchContext = { successUrl: '/good/path', dismissUrl: '/bad/path' };
        spyOn(modal, 'open').and
          .returnValue({
            result: {
              then: function(x, y) { successFunc = x; errFunc = y; }
            }
          });
        func(launchContext);
        successFunc('successUrl');
        expect($window.location.href).toBe('/good/path');
        errFunc('dismissUrl');
        expect($window.location.href).toBe('/bad/path');
      });

      it("doesn't redirect if not configured to", function() {
        var successFunc, errFunc;
        launchContext = {};
        spyOn(modal, 'open').and
          .returnValue({
            result: {
              then: function(x, y) { successFunc = x; errFunc = y; }
            }
          });
        func(launchContext);
        successFunc('successUrl');
        expect($window.location.href).toBe('/');
        errFunc('dismissUrl');
        expect($window.location.href).toBe('/');
      });
    });
  });

})();
