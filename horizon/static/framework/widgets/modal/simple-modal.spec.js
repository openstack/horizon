/**
 * Copyright 2015 IBM Corp.
 * (c) Copyright 2015 Hewlett-Packard Development Company, L.P.
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

(function() {
  "use strict";

  describe('horizon.framework.widgets.simple-modal', function() {

    beforeEach(module('horizon.framework'));

    describe('SimpleModalController', function() {
      var modalInstance, context, ctrl;

      beforeEach(inject(function($controller) {
        modalInstance = {
          close: function() {},
          dismiss: function() {}
        };
        context = { what: 'is it' };
        ctrl = $controller('SimpleModalController',
                           {$modalInstance: modalInstance,
                            context: context});
      }));

      it('establishes a controller', function() {
        expect(ctrl).toBeDefined();
      });

      it('sets context on the modalCtrl variable', function() {
        expect(ctrl.context).toBeDefined();
        expect(ctrl.context).toEqual({ what: 'is it' });
      });

      it('sets action functions', function() {
        expect(ctrl.submit).toBeDefined();
        expect(ctrl.cancel).toBeDefined();
      });

      it('makes submit close the modal instance', function() {
        expect(ctrl.submit).toBeDefined();
        spyOn(modalInstance, 'close');
        ctrl.submit();
        expect(modalInstance.close.calls.count()).toBe(1);
      });

      it('makes cancel close the modal instance', function() {
        expect(ctrl.cancel).toBeDefined();
        spyOn(modalInstance, 'dismiss');
        ctrl.cancel();
        expect(modalInstance.dismiss).toHaveBeenCalledWith('cancel');
      });

    });

    describe('horizon.framework.widgets.modal.simple-modal.service', function() {
      var service, modal;

      beforeEach(module(function($provide) {
        modal = { open: function() {return 'val';} };
        $provide.value('$modal', modal);
      }));

      beforeEach(inject(function($injector) {
        service = $injector.get('horizon.framework.widgets.modal.simple-modal.service');
      }));

      it('defines the service', function() {
        expect(service).toBeDefined();
      });

      it('returns undefined if called with no parameters', function() {
        expect(service.modal()).toBeUndefined();
      });

      it('returns undefined if called without required parameters', function() {
        expect(service.modal({title: {}})).toBeUndefined();
        expect(service.modal({body: {}})).toBeUndefined();
      });

      describe('Maximal Values Passed to the Modal', function() {

        var passed, passedContext;

        beforeEach(function() {
          var opts = { title: 'my title', body: 'my body', submit: 'Yes',
                       cancel: 'No' };
          spyOn(modal, 'open');
          service.modal(opts);
          passed = modal.open.calls.argsFor(0)[0];
          passedContext = passed.resolve.context();
        });

        it('sets the controller', function() {
          expect(passed.controller).toBe('SimpleModalController as modalCtrl');
        });

        it('sets the template URL', function() {
          expect(passed.templateUrl).toBe('/static/framework/widgets/modal/simple-modal.html');
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

        var passed, passedContext;

        beforeEach(function() {
          var opts = { title: 'my title', body: 'my body' };
          spyOn(modal, 'open');
          service.modal(opts);
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
