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
  "use strict";

  describe('hz.widget.modal module', function() {

    beforeEach(module('hz.widget.modal'));

    describe('simpleModalCtrl', function() {
      var scope, modalInstance, context, ctrl;

      beforeEach(inject(function($controller) {
        scope = {};
        modalInstance = {
          close: function() {},
          dismiss: function() {}
        };
        context = { what: 'is it' };
        ctrl = $controller('simpleModalCtrl',
                           {$scope: scope, $modalInstance: modalInstance,
                            context: context});
      }));

      it('establishes a controller', function() {
        expect(ctrl).toBeDefined();
      });

      it('sets context on the scope', function() {
        expect(scope.context).toBeDefined();
        expect(scope.context).toEqual({ what: 'is it' });
      });

      it('sets action functions', function() {
        expect(scope.submit).toBeDefined();
        expect(scope.cancel).toBeDefined();
      });

      it('makes submit close the modal instance', function() {
        expect(scope.submit).toBeDefined();
        spyOn(modalInstance, 'close');
        scope.submit();
        expect(modalInstance.close.calls.count()).toBe(1);
      });

      it('makes cancel close the modal instance', function() {
        expect(scope.cancel).toBeDefined();
        spyOn(modalInstance, 'dismiss');
        scope.cancel();
        expect(modalInstance.dismiss).toHaveBeenCalledWith('cancel');
      });

    });

    describe('simpleModalService', function() {
      var service, modal;

      beforeEach(module(function($provide) {
        modal = { open: function() {return 'val';} };
        $provide.value('basePath', '/this/path/');
        $provide.value('$modal', modal);
      }));

      beforeEach(inject(function(simpleModalService) {
        service = simpleModalService;
      }));

      it('defines the service', function() {
        expect(service).toBeDefined();
      });

      it('returns undefined if called with no parameters', function() {
        expect(service()).toBeUndefined();
      });

      it('returns undefined if called without required parameters', function() {
        expect(service({title: {}})).toBeUndefined();
        expect(service({body: {}})).toBeUndefined();
      });

      describe('Maximal Values Passed to the Modal', function() {

        var returned, passed, passedContext;

        beforeEach(function() {
          var opts = { title: 'my title', body: 'my body', submit: 'Yes',
                       cancel: 'No' };
          spyOn(modal, 'open');
          returned = service(opts);
          passed = modal.open.calls.argsFor(0)[0];
          passedContext = passed.resolve.context();
        });

        it('sets the controller', function() {
          expect(passed.controller).toBe('simpleModalCtrl');
        });

        it('sets the template URL', function() {
          expect(passed.templateUrl).toBe('/this/path/modal/simple-modal.html');
        });

        it('sets the title', function() {
          expect(passedContext.title).toBe('my title');
        });

        it('sets the body', function() {
          expect(passedContext.body).toBe('my body');
        });

        it('sets the submit', function() {
          expect(passedContext.submit).toBe('Yes');
        });

        it('sets the cancel', function() {
          expect(passedContext.cancel).toBe('No');
        });

      });

      describe('Minimal Values Passed to the Modal', function() {

        var returned, passed, passedContext;

        beforeEach(function() {
          var opts = { title: 'my title', body: 'my body' };
          spyOn(modal, 'open');
          returned = service(opts);
          passed = modal.open.calls.argsFor(0)[0];
          passedContext = passed.resolve.context();
        });

        it('sets the title', function() {
          expect(passedContext.title).toBe('my title');
        });

        it('sets the body', function() {
          expect(passedContext.body).toBe('my body');
        });

        it('defaults the submit', function() {
          expect(passedContext.submit).toBe('Submit');
        });

        it('defaults the cancel', function() {
          expect(passedContext.cancel).toBe('Cancel');
        });

      });

    });

  });

})();
