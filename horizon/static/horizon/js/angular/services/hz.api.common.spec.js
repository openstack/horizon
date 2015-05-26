/*global angular,describe,it,expect,inject,module,beforeEach,afterEach*/
(function () {
  'use strict';

  describe('hz.api.common module', function() {
    it('should have been defined', function () {
      expect(angular.module('hz.api.common')).toBeDefined();
    });
  });

  describe('api service', function () {
    var api, $httpBackend;

    beforeEach(module('hz.api.common'));
    beforeEach(inject(function ($injector) {
      api = $injector.get('hz.api.common.service');
      $httpBackend = $injector.get('$httpBackend');
    }));

    afterEach(function() {
      $httpBackend.verifyNoOutstandingExpectation();
    });

    it('should be defined', function () {
      expect(!!api).toBe(true);
    });

    it('should call success on a good response', function () {
      var called = {};
      $httpBackend.when('GET', '/good').respond({status: 'good'});
      $httpBackend.expectGET('/good');
      api.get('/good').success(function (data) {called.data = data;});
      $httpBackend.flush();
      expect(called.data.status).toBe('good');
    });

    it('should call error on a bad response', function () {
      var called = {};
      $httpBackend.when('GET', '/bad').respond(500, '');
      $httpBackend.expectGET('/bad');
      api.get('/bad').error(function () {called.called = true;});
      $httpBackend.flush();
      expect(called.called).toBe(true);
    });

  });
}());