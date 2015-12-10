/*
 * Copyright 2015 IBM Corp
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
  'use strict';

  describe('horizon.framework.widgets.toast module', function() {
    it('should have been defined', function () {
      expect(angular.module('horizon.framework.widgets.toast')).toBeDefined();
    });
  });

  describe('toast factory', function() {

    var $timeout, service;

    var successMsg = "I am success.";
    var dangerMsg = "I am danger.";
    var infoMsg = "I am info.";
    var errorMsg = "I am error.";

    beforeEach(module('templates'));
    beforeEach(module('horizon.framework'));
    beforeEach(inject(function ($injector) {
      service = $injector.get('horizon.framework.widgets.toast.service');
      $timeout = $injector.get('$timeout');
    }));

    it('should create different toasts', function() {
      service.add('danger', dangerMsg);
      expect(service.get().length).toBe(1);
      expect(service.get()[0].type).toBe('danger');
      service.add('success', successMsg);
      expect(service.get().length).toBe(2);
      expect(service.get()[1].type).toBe('success');
      service.add('info', infoMsg);
      expect(service.get().length).toBe(3);
      expect(service.get()[2].msg).toBe(infoMsg);
      service.add('error', errorMsg);
      expect(service.get().length).toBe(4);
      expect(service.get()[3].type).toBe('danger');
      expect(service.get()[3].msg).toBe(errorMsg);

    });

    it('should dismiss specific toasts after a delay', function() {
      service.add('danger', dangerMsg);
      service.add('success', successMsg);
      service.add('info', infoMsg);
      expect(service.get().length).toBe(3);

      $timeout.flush();

      expect(service.get().length).toBe(1);
      expect(service.get()[0].type).toBe('danger');
    });

    it('should provide a function to clear all toasts', function() {
      service.add('success', successMsg);
      service.add('success', successMsg);
      service.add('info', infoMsg);
      expect(service.get().length).toBe(3);
      service.clearAll();
      expect(service.get().length).toBe(0);
    });

    it('should provide a function to clear all error toasts', function() {
      service.add('danger', dangerMsg);
      service.add('success', successMsg);
      service.add('danger', dangerMsg);
      service.add('error', errorMsg);
      expect(service.get().length).toBe(4);
      service.clearErrors();
      expect(service.get().length).toBe(1);
      expect(service.get()[0].type).toBe('success');
    });

    it('should provide a function to clear all success toasts', function() {
      service.add('success', successMsg);
      service.add('success', successMsg);
      service.add('info', infoMsg);
      expect(service.get().length).toBe(3);
      service.clearSuccesses();
      expect(service.get().length).toBe(1);
      expect(service.get()[0].type).toBe('info');
    });

    it('should provide a function to clear a specific toast', function() {
      service.add('success', successMsg);
      service.add('info', infoMsg);
      service.cancel(1);
      expect(service.get().length).toBe(1);
      expect(service.get()[0].type).not.toEqual('info');
    });
  });

  describe('toast directive', function () {

    var $compile,
      $scope,
      $element,
      service;

    var successMsg = "I am success.";
    var dangerMsg = "I am danger.";
    var infoMsg = "I am info.";
    var errorMsg = "I am error.";

    function toasts() {
      return $element.find('.alert');
    }

    beforeEach(module('templates'));
    beforeEach(module('horizon.framework'));
    beforeEach(inject(function ($injector) {
      $scope = $injector.get('$rootScope').$new();
      $compile = $injector.get('$compile');
      service = $injector.get('horizon.framework.widgets.toast.service');

      var markup = '<toast></toast>';
      $element = $compile(markup)($scope);
      $scope.$apply();
    }));

    it('should create toasts using ng-repeat', function() {
      service.add('danger', dangerMsg);
      service.add('success', successMsg);
      service.add('info', infoMsg);
      service.add('error', errorMsg);
      $scope.$apply();
      expect(toasts().length).toBe(4);
    });

    it('should have the proper classes for different toasts types', function() {
      service.add('danger', dangerMsg);
      service.add('success', successMsg);
      service.add('info', infoMsg);
      service.add('error', errorMsg);
      $scope.$apply();
      expect(toasts().length).toBe(4);
      expect(toasts().eq(0).hasClass('alert-danger'));
      expect(toasts().eq(1).hasClass('alert-success'));
      expect(toasts().eq(2).hasClass('alert-info'));
      expect(toasts().eq(3).hasClass('alert-danger'));
    });

    it('should be possible to remove a toast by clicking close', function() {
      service.add('success', successMsg);
      $scope.$apply();
      expect(toasts().length).toBe(1);
      toasts().eq(0).find('.close').click();
      $scope.$apply();
      expect(toasts().length).toBe(0);
    });
  });
})();
