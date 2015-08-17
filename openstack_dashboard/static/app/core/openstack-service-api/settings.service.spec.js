/*
 * (c) Copyright 2015 Hewlett-Packard Development Company, L.P.
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
(function () {
  'use strict';

  horizon.alert = angular.noop;

  var $httpBackend;
  var responseMockOpts = {succeed: true};
  var testData = {
    isTrue: true,
    isFalse: false,
    versions: {one: 1, two: 2},
    deep: {nest: {foo: 'bar'}},
    isNull: null
  };

  function responseMockReturn() {
    return responseMockOpts.succeed ? [200, testData, {}] : [500, 'Fail', {}];
  }

  describe('horizon.app.core.openstack-service-api.settings', function () {
    var settingsService;

    beforeEach(module('horizon.app.core.openstack-service-api'));

    beforeEach(module('horizon.framework.util.http'));

    beforeEach(inject(function (_$httpBackend_, $injector) {
      responseMockOpts.succeed = true;
      settingsService = $injector.get('horizon.app.core.openstack-service-api.settings');
      $httpBackend = _$httpBackend_;
      $httpBackend.whenGET('/api/settings/').respond(responseMockReturn);
      $httpBackend.expectGET('/api/settings/');
    }));

    afterEach(function () {
      $httpBackend.verifyNoOutstandingExpectation();
      $httpBackend.verifyNoOutstandingRequest();
    });

    describe('getSettings', function () {

      it('should return all settings', function () {
        settingsService.getSettings().then(
          function (actual) {
            expect(actual).toEqual(testData);
          }
        );
        $httpBackend.flush();
      });

      it('should fail when error response', function () {
        responseMockOpts.succeed = false;
        spyOn(horizon, 'alert');
        settingsService.getSettings().then(
          function (actual) {
            fail('Should not have succeeded: ' + angular.toJson(actual));
          },
          function (actual) {
            expect(actual).toBeDefined();
          }
        );
        $httpBackend.flush();
        expect(horizon.alert).toHaveBeenCalledWith('error',
          gettext('Unable to retrieve settings.'));
      });

      it('should suppress error messages if asked', function () {
        responseMockOpts.succeed = false;
        spyOn(horizon, 'alert');
        settingsService.getSettings(true).then(
          function (actual) {
            fail('Should not have succeeded: ' + angular.toJson(actual));
          },
          function (actual) {
            expect(actual).toBeDefined();
          }
        );
        $httpBackend.flush();
        expect(horizon.alert).not.toHaveBeenCalled();
      });

    });

    describe('getSetting', function () {

      it('nested deep object is found', function () {
        settingsService.getSetting('deep.nest.foo')
          .then(function (actual) {
            expect(actual).toEqual('bar');
          });
        $httpBackend.flush();
      });

      it("is undefined when doesn't exist", function () {
        settingsService.getSetting('will.not.exist')
          .then(function (actual) {
            expect(actual).toBeUndefined();
          });
        $httpBackend.flush();
      });

      it("default is returned when doesn't exist", function () {
        settingsService.getSetting('will.not.exist', 'hello')
          .then(function (actual) {
            expect(actual).toEqual('hello');
          });
        $httpBackend.flush();
      });

      it('should return true', function () {
        settingsService.getSetting('isTrue')
          .then(function (actual) {
            expect(actual).toEqual(true);
          });
        $httpBackend.flush();
      });

      it('should fail when error response', function () {
        responseMockOpts.succeed = false;
        settingsService.getSetting('isTrue').then(
          function (actual) {
            fail('Should not have succeeded: ' + angular.toJson(actual));
          },
          function (actual) {
            expect(actual).toBeDefined();
          }
        );
        $httpBackend.flush();
      });

    });

    describe('ifEnabled', function () {

      var expectedResult = {};

      var enabled = function () {
        expectedResult.enabled = true;
      };

      var notEnabled = function () {
        expectedResult.enabled = false;
      };

      beforeEach(inject(function () {
        expectedResult = {enabled: null};
      }));

      function meetsExpectations(expected) {
        $httpBackend.flush();
        expect(expectedResult.enabled).toBe(expected);
      }

      it('should fail when error response', function () {
        responseMockOpts.succeed = false;
        settingsService.ifEnabled('isTrue').then(
          function (actual) {
            fail('Should not have succeeded: ' + angular.toJson(actual));
          },
          function (actual) {
            expect(actual).toBeDefined();
          }
        );
        $httpBackend.flush();
      });

      it('boolean is enabled when true', function () {
        settingsService.ifEnabled('isTrue').then(enabled, notEnabled);
        meetsExpectations(true);
      });

      it('boolean is enabled when true expected', function () {
        settingsService.ifEnabled('isTrue', true).then(enabled, notEnabled);
        meetsExpectations(true);
      });

      it('boolean is not enabled when false expected', function () {
        settingsService.ifEnabled('isTrue', false).then(enabled, notEnabled);
        meetsExpectations(false);
      });

      it('boolean is not enabled when false', function () {
        settingsService.ifEnabled('isFalse').then(enabled, notEnabled);
        meetsExpectations(false);
      });

      it('boolean is enabled when false expected', function () {
        settingsService.ifEnabled('isFalse', false).then(enabled, notEnabled);
        meetsExpectations(true);
      });

      it('nested object is enabled when expected', function () {
        settingsService.ifEnabled('versions.one', 1).then(enabled, notEnabled);
        meetsExpectations(true);
      });

      it('nested object is not enabled', function () {
        settingsService.ifEnabled('versions.two', 1).then(enabled, notEnabled);
        meetsExpectations(false);
      });

      it('nested object is not enabled when not found', function () {
        settingsService.ifEnabled('no-exist.two', 1).then(enabled, notEnabled);
        meetsExpectations(false);
      });

      it('nested deep object is enabled when expected', function () {
        settingsService.ifEnabled('deep.nest.foo', 'bar').then(enabled, notEnabled);
        meetsExpectations(true);
      });

      it('nested deep object is not enabled when not expected', function () {
        settingsService.ifEnabled('deep.nest.foo', 'wrong').then(enabled, notEnabled);
        meetsExpectations(false);
      });

      it('null is not enabled', function () {
        settingsService.ifEnabled('isNull').then(enabled, notEnabled);
        meetsExpectations(false);
      });

      it('null is enabled when expected', function () {
        settingsService.ifEnabled('isNull', null).then(enabled, notEnabled);
        meetsExpectations(true);
      });

      it('true is enabled when not found and true default', function () {
        settingsService.ifEnabled('nonExistent', true, true).then(enabled, notEnabled);
        meetsExpectations(true);
      });

      it('true is not enabled when not found and false default', function () {
        settingsService.ifEnabled('nonExistent', true, false).then(enabled, notEnabled);
        meetsExpectations(false);
      });

      it('true is not enabled when not found and no default', function () {
        settingsService.ifEnabled('nonExistent', true).then(enabled, notEnabled);
        meetsExpectations(false);
      });

      it('false is enabled when not found and expected w/ default', function () {
        settingsService.ifEnabled('nonExistent', false, false).then(enabled, notEnabled);
        meetsExpectations(true);
      });

      it('bar is enabled when expected not found and bar default', function () {
        settingsService.ifEnabled('nonExistent', 'bar', 'bar').then(enabled, notEnabled);
        meetsExpectations(true);
      });

      it('bar is not enabled when expected not found and not default', function () {
        settingsService.ifEnabled('nonExistent', 'bar', 'foo').then(enabled, notEnabled);
        meetsExpectations(false);
      });
    });

  });

})();
