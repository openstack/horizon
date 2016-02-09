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

    var service, $scope, $element, markup;

    var expectedTemplateResult =
      '<!-- Maintain parity with _loading_modal.html -->\n' +
      '<div class="modal-body">\n  <span class="loader fa fa-spinner ' +
      'fa-spin fa-5x text-center"></span>\n  <div class="loader-caption h4 text-center">' +
      'wait&hellip;</div>\n</div>\n';

    beforeEach(module('ui.bootstrap'));
    beforeEach(module('templates'));
    beforeEach(module('horizon.framework'));

    beforeEach(inject(function ($injector) {
      var $compile = $injector.get('$compile');
      var $templateCache = $injector.get('$templateCache');
      var basePath = $injector.get('horizon.framework.widgets.basePath');

      $scope = $injector.get('$rootScope').$new();
      service = $injector.get('horizon.framework.widgets.modal-wait-spinner.service');

      markup = $templateCache
          .get(basePath + 'modal-wait-spinner/modal-wait-spinner.template.html');

      $element = angular.element(markup);
      $compile($element)($scope);

      $scope.$apply();
    }));

    it('returns the service', function() {
      expect(service).toBeDefined();
    });

    describe('showModalSpinner', function() {

      it('is defined', function() {
        expect(service.showModalSpinner).toBeDefined();
      });

      it('opens modal with the correct object', inject(function($uibModal) {
        spyOn($uibModal, 'open').and.callThrough();
        service.showModalSpinner('wait');
        $scope.$apply();

        expect($uibModal.open).toHaveBeenCalled();
        expect($uibModal.open.calls.count()).toEqual(1);
        expect($uibModal.open.calls.argsFor(0)[0].backdrop).toEqual('static');
        expect($uibModal.open.calls.argsFor(0)[0].template).toEqual(expectedTemplateResult);
        expect($uibModal.open.calls.argsFor(0)[0].windowClass).toEqual('modal-wait-spinner');
      }));
    });

    describe('hideModalSpinner', function() {

      it('has hideModalSpinner', function() {
        expect(service.hideModalSpinner).toBeDefined();
      });

      it("dismisses modal when it has been opened", inject(function($uibModal) {
        var modal = {dismiss: function() {}};
        spyOn($uibModal, 'open').and.returnValue(modal);
        service.showModalSpinner('asdf');

        spyOn(modal, 'dismiss');
        service.hideModalSpinner();

        expect(modal.dismiss).toHaveBeenCalled();
      }));
    });
  });

  describe('Wait Spinner Directive', function() {
    var $scope, $element;

    beforeEach(module('ui.bootstrap'));
    beforeEach(module('templates'));
    beforeEach(module('horizon.framework'));

    beforeEach(inject(function($injector) {
      var $compile = $injector.get('$compile');
      $scope = $injector.get('$rootScope').$new();

      var markup = '<div wait-spinner text="hello!"></div>';
      $element = angular.element(markup);
      $compile($element)($scope);
      $scope.$apply();
    }));

    it("creates a div element with correct text", function() {
      var elems = $element.find('div div');
      expect(elems.length).toBe(1);
      //The spinner is a nested div with the "text" set according to the attribute
      //indexOf is used because the spinner puts &hellip;  after the text, however
      //jasmine does not convert &hellip; to the three dots and thinks they don't match
      //when compared with toEqual
      expect(elems[0].innerText.indexOf('hello!')).toBe(0);
    });
  });
})();
