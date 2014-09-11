/*global describe, it, expect, jasmine, beforeEach, spyOn, angular*/
describe('metadata-widget-controller', function () {
  'use strict';
  var $scope;
  beforeEach(function () {
    angular.mock.module('hz');
  });

  beforeEach(function () {
    angular.mock.inject(function ($injector) {
      var gettext = function (text) {
        return text;
      };
      var $window = {
        available_metadata: {namespaces: []},
        gettext: gettext
      };
      $scope = $injector.get('$rootScope').$new();
      var metadataController = $injector.get('$controller')(
        'hzMetadataWidgetCtrl',
        {
          $scope: $scope,
          $window: $window
        });
    });
  });

  describe('formatErrorMessage', function () {
    it('should return undefined', function () {
      expect($scope.formatErrorMessage('test', 'test')).toBe(undefined);
    });

    it('should return "Min 2"', function () {
      var error, item;
      error = {min: true};
      item = {leaf: {minimum: '2'}};
      expect($scope.formatErrorMessage(item, error)).toBe('Min 2');
    });

    it('should return "Max 2"', function () {
      var error, item;
      error = {max: true};
      item = {leaf: {maximum: '2'}};
      expect($scope.formatErrorMessage(item, error)).toBe('Max 2');
    });

    it('should return "Min length 5"', function () {
      var error, item;
      error = {minlength: true};
      item = {leaf: {minLength: '5'}};
      expect($scope.formatErrorMessage(item, error)).toBe('Min length 5');
    });

    it('should return "Max length 5"', function () {
      var error, item;
      error = {maxlength: true};
      item = {leaf: {maxLength: '5'}};
      expect($scope.formatErrorMessage(item, error)).toBe('Max length 5');
    });

    it('should return "Integer required"', function () {
      var error, item;
      error = {pattern: true};
      item = {leaf: {type: 'integer'}};
      expect($scope.formatErrorMessage(item, error)).toBe('Integer required');
    });

    it('should return "Pattern mismatch"', function () {
      var error, item;
      error = {pattern: true};
      item = {leaf: {type: 'wrong pattern'}};
      expect($scope.formatErrorMessage(item, error)).toBe('Pattern mismatch');
    });

    it('should return "Integer required"', function () {
      var error, item;
      error = {required: true};
      item = {leaf: {type: 'integer'}};
      expect($scope.formatErrorMessage(item, error)).toBe('Integer required');
    });

    it('should return "Decimal required"', function () {
      var error, item;
      error = {required: true};
      item = {leaf: {type: 'number'}};
      expect($scope.formatErrorMessage(item, error)).toBe('Decimal required');
    });

    it('should return "Integer required"', function () {
      var error, item;
      error = {required: true};
      item = {leaf: {type: 'mock'}};
      expect($scope.formatErrorMessage(item, error)).toBe('Required');
    });
  });
});
