/**
 * Copyright 2016 Cisco Systems
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

  describe('contenteditable directive', function() {
    var $compile, $scope;

    beforeEach(module('horizon.framework.widgets'));
    beforeEach(module('horizon.framework.widgets.contenteditable'));
    beforeEach(inject(function ($injector) {
      $compile = $injector.get('$compile');
      $scope = $injector.get('$rootScope').$new();
      $scope.testData = '';
    }));

    describe('using a model', function() {
      var element;
      beforeEach(function before() {
        element = $compile('<pre contenteditable ng-model="testData"></pre>')($scope);
        $scope.$digest();
      });

      it('should update the model when content is edited', function () {
        element.triggerHandler('focus');
        element.html('foo');
        $scope.$digest();
        element.triggerHandler('blur');
        expect($scope.testData).toBe('foo');
      });

      it('should update the view when model is changed', function () {
        element.triggerHandler('focus');
        $scope.testData = 'spam';
        $scope.$digest();

        expect(element.html()).toBe('spam');
      });
    });

    it('should not do anything without an accompanying ng-model', function() {
      var element = $compile('<pre contenteditable></pre>')($scope);
      $scope.$digest();

      element.triggerHandler('focus');
      element.html('bar');
      $scope.$digest();
      element.triggerHandler('blur');

      expect($scope.testData).toBe('');
    });
  });
})();
