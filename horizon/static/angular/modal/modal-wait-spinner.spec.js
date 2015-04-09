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

  describe('Wait Spinner Tests', function() {

    var service, modal;

    beforeEach(module('hz.widget.modal-wait-spinner'));

    beforeEach(inject(function(modalWaitSpinnerService, $modal) {
      service = modalWaitSpinnerService;
      modal = $modal;
    }));

    it('returns the service', function() {
      expect(service).toBeDefined();
    });

    describe('showModalSpinner', function() {

      it('is defined', function() {
        expect(service.showModalSpinner).toBeDefined();
      });

      it('opens modal with the correct object', inject(function($modal) {
        var wanted = { backdrop: 'static',
                       template: '<div wait-spinner class="modal-body" text="my text"></div>',
                       windowClass: 'modal-wait-spinner modal_wrapper loading'
                     };
        spyOn($modal, 'open');
        service.showModalSpinner('my text');
        expect($modal.open).toHaveBeenCalled();
        expect($modal.open.calls.count()).toBe(1);
        expect($modal.open.calls.argsFor(0)).toEqual([wanted]);
      }));

    });

    describe('hideModalSpinner', function() {

      it('has hideModalSpinner', function() {
        expect(service.hideModalSpinner).toBeDefined();
      });

      it("dismisses modal when it has been opened", inject(function($modal) {
        var modal = {dismiss: function() {}};
        spyOn($modal, 'open').and.returnValue(modal);
        service.showModalSpinner('asdf');
        spyOn(modal, 'dismiss');
        service.hideModalSpinner();
        expect(modal.dismiss).toHaveBeenCalled();
      }));

    });

  });

  describe('Wait Spinner Directive', function() {
    var $scope, $element, $timeout;

    beforeEach(module('ui.bootstrap'));
    beforeEach(module('hz.widget.modal-wait-spinner'));

    beforeEach(inject(function($injector) {
      var $compile = $injector.get('$compile');
      $scope = $injector.get('$rootScope').$new();
      $timeout = $injector.get('$timeout');

      var markup = '<div wait-spinner text="hello!"></div>';
      $element = angular.element(markup);
      $compile($element)($scope);

      $scope.$digest();
    }));

    it("creates a p element", function() {
      var elems = $element.find('p');
      expect(elems.length).toBe(1);
    });

  });

})();
