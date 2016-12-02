/**
 * Licensed under the Apache License, Version 2.0 (the "License"); you may
 * not use this file except in compliance with the License. You may obtain
 * a copy of the License at
 *
 *    http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
 * WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
 * License for the specific language governing permissions and limitations
 * under the License.
 */

(function () {
  'use strict';

  describe('horizon.framework.util.http module', function() {
    it('should have been defined', function () {
      expect(angular.module('horizon.framework.util.http')).toBeDefined();
    });
  });

  describe('api service', function () {
    var api, $httpBackend;
    var WEBROOT = '/horizon/';

    beforeEach(module('horizon.framework', function($provide) {
      $provide.value('$window', {WEBROOT: WEBROOT});
    }));
    beforeEach(inject(function ($injector) {
      api = $injector.get('horizon.framework.util.http.service');
      $httpBackend = $injector.get('$httpBackend');
    }));

    afterEach(function () {
      $httpBackend.verifyNoOutstandingExpectation();
    });

    it('should be defined', function () {
      expect(!!api).toBe(true);
    });

    function testGoodCall(apiMethod, verb, data) {
      var called = {};
      var url = WEBROOT + 'good';
      data = data || 'some complicated data';
      var suppliedData = verb === 'GET' ? undefined : data;
      $httpBackend.when(verb, url, suppliedData).respond({status: 'good'});
      $httpBackend.expect(verb, url, suppliedData);
      apiMethod('/good', suppliedData).success(function (data) {
        called.data = data;
      });
      $httpBackend.flush();
      expect(called.data.status).toBe('good');
    }

    function testBadCall(apiMethod, verb) {
      var called = {};
      var url = WEBROOT + 'bad';
      var suppliedData = verb === 'GET' ? undefined : 'some complicated data';
      $httpBackend.when(verb, url, suppliedData).respond(500, '');
      $httpBackend.expect(verb, url, suppliedData);
      apiMethod('/bad', suppliedData).error(function () {
        called.called = true;
      });
      $httpBackend.flush();
      expect(called.called).toBe(true);
    }

    it('should call success on a good GET response', function () {
      testGoodCall(api.get, 'GET');
    });

    it('should call error on a bad GET response', function () {
      testBadCall(api.get, 'GET');
    });

    it('should call success on a good POST response', function () {
      testGoodCall(api.post, 'POST');
    });

    it('should call error on a bad POST response', function () {
      testBadCall(api.post, 'POST');
    });

    it('should call success on a good PATCH response', function () {
      testGoodCall(api.patch, 'PATCH');
    });

    it('should call error on a bad PATCH response', function () {
      testBadCall(api.patch, 'PATCH');
    });

    it('should call success on a good PUT response', function () {
      testGoodCall(api.put, 'PUT');
    });

    it('should call error on a bad PUT response', function () {
      testBadCall(api.put, 'PUT');
    });

    it('should call success on a good DELETE response', function () {
      testGoodCall(api.delete, 'DELETE');
    });

    it('should call error on a bad DELETE response', function () {
      testBadCall(api.delete, 'DELETE');
    });

    describe('WEBROOT handling', function() {
      it('respects WEBROOT by default', function() {
        var expectedUrl = WEBROOT + 'good';
        var $scope = {};
        $httpBackend.when('GET', expectedUrl).respond(200, '');
        $httpBackend.expect('GET', expectedUrl);
        api.get('/good').success(function() {
          $scope.success = true;
        });

        $httpBackend.flush();
        expect($scope.success).toBe(true);
      });

      it('ignores WEBROOT with external = true flag', function() {
        var expectedUrl = '/good';
        var $scope = {};
        $httpBackend.when('GET', expectedUrl).respond(200, '');
        $httpBackend.expect('GET', expectedUrl);
        api.get('/good', {external: true}).success(function() {
          $scope.success = true;
        });

        $httpBackend.flush();
        expect($scope.success).toBe(true);
      });
    });

    describe('Upload service', function () {
      var Upload, file;
      var called = {};

      beforeEach(inject(function ($injector) {
        Upload = $injector.get('Upload');
        spyOn(Upload, 'upload').and.callFake(function (config) {
          called.config = config;
        });
        spyOn(Upload, 'http').and.callFake(function (config) {
          called.config = config;
        });
        file = new File(['part'], 'filename.sample');
      }));

      it('upload() is used when there is a File() blob inside data', function () {
        api.post('/good', {first: file, second: 'the data'});
        expect(Upload.upload).toHaveBeenCalled();

        var expected = {first: file, second: 'the data'};
        expected.$$originalJSON = JSON.stringify(expected);
        expect(called.config.data).toEqual(expected);
      });

      it('upload() is NOT used when a File() blob is passed as data', function () {
        api.post('/good', file);
        expect(Upload.upload).not.toHaveBeenCalled();
      });

      it('upload() is NOT used in case there are no File() blobs inside data', function() {
        testGoodCall(api.post, 'POST', {second: 'the data'});
        expect(Upload.upload).not.toHaveBeenCalled();
      });

      it('upload() respects WEBROOT by default', function() {
        api.post('/good', {first: file});
        expect(called.config.url).toEqual(WEBROOT + 'good');
      });

      it('upload() ignores WEBROOT with external = true flag', function() {
        api.post('/good', {first: file}, {external: true});
        expect(called.config.url).toEqual('/good');
      });

      it('http() is used when a File() blob is passed as data', function () {
        api.post('/good', file);
        expect(Upload.http).toHaveBeenCalled();
        expect(called.config.data).toEqual(file);
      });

      it('http() is NOT used when there is a File() blob inside data', function () {
        api.post('/good', {first: file, second: 'the data'});
        expect(Upload.http).not.toHaveBeenCalled();
      });

      it('http() is NOT used when no File() blobs are passed at all', function() {
        testGoodCall(api.post, 'POST', {second: 'the data'});
        expect(Upload.http).not.toHaveBeenCalled();
      });

      it('http() respects WEBROOT by default', function() {
        api.post('/good', file);
        expect(called.config.url).toEqual(WEBROOT + 'good');
      });

      it('http() ignores WEBROOT with external = true flag', function() {
        api.post('/good', file, {external: true});
        expect(called.config.url).toEqual('/good');
      });

    });
  });
}());
