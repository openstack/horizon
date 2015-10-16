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
  'use strict';

  describe('horizon.framework.widgets.wizard module', function () {
    it('should have been defined', function () {
      expect(angular.module('horizon.framework.widgets.wizard')).toBeDefined();
    });
  });

  describe('wizard directive', function () {
    var $compile,
      $scope,
      element;

    beforeEach(module('templates'));
    beforeEach(module('horizon.framework.widgets'));
    beforeEach(module('horizon.framework.widgets.wizard'));
    beforeEach(inject(function ($injector) {
      $scope = $injector.get('$rootScope').$new();
      $compile = $injector.get('$compile');
      element = $compile('<wizard></wizard>')($scope);
    }));

    it('should be compiled', function () {
      var element = $compile('<wizard>some text</wizard>')($scope);
      $scope.$apply();
      expect(element.html().trim()).not.toBe('some text');
    });

    it('should have empty title by default', function () {
      $scope.workflow = {};
      $scope.$apply();
      expect(element[0].querySelector('.title').textContent).toBe('');
    });

    it('should have title if it is specified by workflow', function () {
      var titleText = 'Some title';
      $scope.workflow = {};
      $scope.workflow.title = titleText;
      $scope.$apply();
      expect(element[0].querySelector('.title').textContent).toBe(titleText);
    });

    it('should contain one help-panel', function () {
      $scope.workflow = {};
      $scope.workflow.title = "doesn't matter";
      $scope.$apply();
      expect(element[0].querySelectorAll('help-panel').length).toBe(1);
    });

    it('should have no steps if no steps defined', function () {
      $scope.workflow = {};
      $scope.$apply();
      expect(element[0].querySelectorAll('.step').length).toBe(0);
    });

    it('should have 3 steps if 3 steps defined', function () {
      $scope.workflow = {
        steps: [ {}, {}, {} ]
      };
      $scope.$apply();
      expect(element[0].querySelectorAll('.step').length).toBe(3);
    });

    it('should have no nav items if no steps defined', function () {
      $scope.workflow = {};
      $scope.$apply();
      expect(element[0].querySelectorAll('.nav-item').length).toBe(0);
    });

    it('should have 3 nav items if 3 steps defined', function () {
      $scope.workflow = {
        steps: [ {}, {}, {} ]
      };
      $scope.$apply();
      expect(element[0].querySelectorAll('.nav-item').length).toBe(3);
    });

    it('should navigate correctly', function () {
      $scope.workflow = {
        steps: [ {}, {}, {} ]
      };

      $scope.$apply();
      expect($scope.currentIndex).toBe(0);
      expect(angular.element(element).find('.step').eq(0).hasClass('ng-hide')).toBe(false);
      expect(angular.element(element).find('.step').eq(1).hasClass('ng-hide')).toBe(true);
      expect(angular.element(element).find('.step').eq(2).hasClass('ng-hide')).toBe(true);
      expect(angular.element(element).find('.nav-item').eq(0).hasClass('current')).toBe(true);
      expect(angular.element(element).find('.nav-item').eq(1).hasClass('current')).toBe(false);
      expect(angular.element(element).find('.nav-item').eq(2).hasClass('current')).toBe(false);

      $scope.switchTo(1);
      $scope.$apply();
      expect($scope.currentIndex).toBe(1);
      expect(angular.element(element).find('.step').eq(0).hasClass('ng-hide')).toBe(true);
      expect(angular.element(element).find('.step').eq(1).hasClass('ng-hide')).toBe(false);
      expect(angular.element(element).find('.step').eq(2).hasClass('ng-hide')).toBe(true);
      expect(angular.element(element).find('.nav-item').eq(0).hasClass('current')).toBe(false);
      expect(angular.element(element).find('.nav-item').eq(1).hasClass('current')).toBe(true);
      expect(angular.element(element).find('.nav-item').eq(2).hasClass('current')).toBe(false);

      $scope.switchTo(2);
      $scope.$apply();
      expect($scope.currentIndex).toBe(2);
      expect(angular.element(element).find('.step').eq(0).hasClass('ng-hide')).toBe(true);
      expect(angular.element(element).find('.step').eq(1).hasClass('ng-hide')).toBe(true);
      expect(angular.element(element).find('.step').eq(2).hasClass('ng-hide')).toBe(false);
      expect(angular.element(element).find('.nav-item').eq(0).hasClass('current')).toBe(false);
      expect(angular.element(element).find('.nav-item').eq(1).hasClass('current')).toBe(false);
      expect(angular.element(element).find('.nav-item').eq(2).hasClass('current')).toBe(true);
    });

    it('should not show back button in step 1/3', function () {
      $scope.workflow = {
        steps: [{}, {}, {}]
      };
      $scope.$apply();
      expect(angular.element(element).find('button.back').hasClass('ng-hide')).toBe(true);
      expect(angular.element(element).find('button.next').hasClass('ng-hide')).toBe(false);
    });

    it('should show both back and next button in step 2/3', function () {
      $scope.workflow = {
        steps: [{}, {}, {}]
      };
      $scope.$apply();
      $scope.switchTo(1);
      $scope.$apply();
      expect(angular.element(element).find('button.back').hasClass('ng-hide')).toBe(false);
      expect(angular.element(element).find('button.next').hasClass('ng-hide')).toBe(false);
    });

    it('should not show next button in step 3/3', function () {
      $scope.workflow = {
        steps: [{}, {}, {}]
      };
      $scope.$apply();
      $scope.switchTo(2);
      $scope.$apply();
      expect(angular.element(element).find('button.back').hasClass('ng-hide')).toBe(false);
      expect(angular.element(element).find('button.next').hasClass('ng-hide')).toBe(true);
    });

    it('should have finish button disabled if wizardForm is invalid', function () {
      $scope.wizardForm = { };
      $scope.$apply();
      $scope.wizardForm.$invalid = true;
      $scope.$apply();
      expect(element[0].querySelector('button.finish').hasAttribute('disabled')).toBe(true);
    });

    it('should have finish button enabled if wizardForm is valid', function () {
      $scope.wizardForm = { };
      $scope.$apply();
      $scope.wizardForm.$invalid = false;
      $scope.$apply();
      expect(element[0].querySelector('button.finish').hasAttribute('disabled')).toBe(false);
    });

    it('should show error message after calling method showError', function () {
      var errorMessage = 'some error message';
      $scope.$apply();
      $scope.showError(errorMessage);
      $scope.$apply();
      expect(element[0].querySelector('.error-message').textContent).toBe(errorMessage);
    });

    it("checks steps' readiness", function() {
      var checkedStep = {checkReadiness: function() { return true; }};
      $scope.workflow = {
        steps: [{}, checkedStep, {}]
      };

      spyOn(checkedStep, 'checkReadiness').and.returnValue({then: function() {}});
      $scope.$apply();
      expect(checkedStep.checkReadiness).toHaveBeenCalled();
    });

  });

  describe("ModalContainerController", function() {
    var ctrl, scope, modalInstance, launchContext;

    beforeEach(module('horizon.framework.widgets.wizard'));

    beforeEach(inject(function($controller) {
      scope = {};
      modalInstance = { close: angular.noop, dismiss: angular.noop };
      launchContext = { my: 'data' };
      ctrl = $controller('ModalContainerController',
                         { $scope: scope, $modalInstance: modalInstance,
                           launchContext: launchContext } );
    }));

    it('is defined', function() {
      expect(ctrl).toBeDefined();
    });

    it('sets scope.launchContext', function() {
      expect(scope.launchContext).toBeDefined();
      expect(scope.launchContext).toEqual({ my: 'data' });
    });

    it('sets scope.close to a function that closes the modal', function() {
      expect(scope.close).toBeDefined();
      spyOn(modalInstance, 'close');
      scope.close();
      expect(modalInstance.close).toHaveBeenCalled();
    });

    it('sets scope.cancel to a function that dismisses the modal', function() {
      expect(scope.cancel).toBeDefined();
      spyOn(modalInstance, 'dismiss');
      scope.cancel();
      expect(modalInstance.dismiss).toHaveBeenCalled();
    });

  });

})();
