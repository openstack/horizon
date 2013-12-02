/*global describe, it, expect, jasmine, beforeEach, spyOn, angular*/
describe('hz.utils', function () {
  'use strict';
  describe('hz.utils.hzUtils', function () {

    beforeEach(function () {
      angular.mock.module('hz.conf');
      angular.mock.module('hz.utils.hzUtils');
    });

    describe('hzUtils', function () {
      var hzUtils;

      beforeEach(function () {
        angular.mock.inject(function ($injector) {
          hzUtils = $injector.get('hzUtils');
        });
      });

      describe('log', function () {
        var hzConfig, $log, log;

        beforeEach(function () {
          log = 'display a log';
          angular.mock.inject(function ($injector) {
            $log = $injector.get('$log');
            hzConfig = $injector.get('hzConfig');
            //jasmine cannot mock properties
            hzConfig.debug = true;
          });
        });

        it('should display a log at default log level', function () {
          hzUtils.log(log);
          expect($log.log.logs.length).toBe(1);
          expect($log.log.logs[0][0]).toBe(log);
        });

        it('should have a configurable log level', function () {
          hzUtils.log(log, 'debug');
          expect($log.debug.logs.length).toBe(1);

          hzUtils.log(log, 'error');
          expect($log.error.logs.length).toBe(1);

          hzUtils.log(log, 'info');
          expect($log.info.logs.length).toBe(1);

          hzUtils.log(log, 'log');
          expect($log.log.logs.length).toBe(1);

          hzUtils.log(log, 'warn');
          expect($log.warn.logs.length).toBe(1);
        });
      });

      describe('capitalize', function () {
        it('should capitalize the first letter of a string', function () {
          expect(hzUtils.capitalize('string to test')).toBe('String to test');
        });
      });

      describe('humanizeNumbers', function () {
        it('should add a comma every three number', function () {
          expect(hzUtils.humanizeNumbers('1234')).toBe('1,234');
          expect(hzUtils.humanizeNumbers('1234567')).toBe('1,234,567');
        });

        it('should work with string or numbers', function () {
          expect(hzUtils.humanizeNumbers('1234')).toBe('1,234');
          expect(hzUtils.humanizeNumbers(1234)).toBe('1,234');
        });

        it('should work with multiple values through a string', function () {
          expect(hzUtils.humanizeNumbers('My Total: 1234')).
            toBe('My Total: 1,234');

          expect(hzUtils.humanizeNumbers('My Total: 1234, His Total: 1234567')).
            toBe('My Total: 1,234, His Total: 1,234,567');
        });
      });

      describe('truncate', function () {
        var string = 'This will be cut', ellipsis = '&hellip;';

        it('should truncate a string at a given length', function () {
          expect(hzUtils.truncate(string, 15)).
            toBe(string.slice(0, 15));
          expect(hzUtils.truncate(string, 20)).
            toBe(string);
        });

        it('should add an ellipsis if needed ', function () {
          expect(hzUtils.truncate(string, 15, true)).
            toBe(string.slice(0, 12) + ellipsis);

          expect(hzUtils.truncate(string, 20, true)).
            toBe(string);

          expect(hzUtils.truncate(string, 2, true)).
            toBe(ellipsis);
        });
      });

      describe('loadAngular', function () {
        var rootScope, element;

        beforeEach(function () {
          element = angular.element('<div>');

          angular.mock.inject(function ($injector) {
            rootScope = $injector.get('$rootScope');
          });
          spyOn(rootScope, '$apply');
        });

        it('should call a compile and apply ', function () {
          hzUtils.loadAngular(element);
          //checks the use of apply function
          expect(rootScope.$apply).toHaveBeenCalled();
          //checks the use of compile function
          expect(element.hasClass('ng-scope')).toBeTruthy();
        });
      });
    });
  });
});