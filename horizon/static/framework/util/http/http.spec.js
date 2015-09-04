(function () {
  'use strict';

  describe('horizon.framework.util.http module', function() {
    it('should have been defined', function () {
      expect(angular.module('horizon.framework.util.http')).toBeDefined();
    });
  });

  describe('api service', function () {
    var api, $httpBackend;

    beforeEach(module('horizon.framework'));
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

    function testGoodCall(apiMethod, verb) {
      var called = {};
      var suppliedData = verb === 'GET' ? undefined : 'some complicated data';
      $httpBackend.when(verb, '/good', suppliedData).respond({status: 'good'});
      $httpBackend.expect(verb, '/good', suppliedData);
      apiMethod('/good', suppliedData).success(function (data) {
        called.data = data;
      });
      $httpBackend.flush();
      expect(called.data.status).toBe('good');
    }

    function testBadCall(apiMethod, verb) {
      var called = {};
      var suppliedData = verb === 'GET' ? undefined : 'some complicated data';
      $httpBackend.when(verb, '/bad', suppliedData).respond(500, '');
      $httpBackend.expect(verb, '/bad', suppliedData);
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

  });
}());
