/*
 *    (c) Copyright 2016 Rackspace US, Inc
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

  describe('horizon.dashboard.project.containers model', function() {
    beforeEach(module('horizon.dashboard.project.containers'));

    var $compile, $scope;

    beforeEach(inject(function inject($injector, _$rootScope_) {
      $scope = _$rootScope_.$new();
      $compile = $injector.get('$compile');
    }));

    it('should detect changes to file selection and update things', function test() {
      // set up scope for the elements below
      $scope.model = '';
      $scope.changed = angular.noop;
      spyOn($scope, 'changed');

      var element = angular.element(
        '<div><input type="file" on-file-change="changed" ng-model="model" />' +
        '<span>{{ model }}</span></div>'
      );
      element = $compile(element)($scope);
      $scope.$apply();

      // generate a file change event with a "file" selected
      var files = [{name: 'test.txt', size: 1}];
      element.find('input').triggerHandler({
        type: 'change',
        target: {files: files}
      });

      expect($scope.changed).toHaveBeenCalled();
      expect($scope.model).toEqual('test.txt');
      expect(element.find('span').text()).toEqual('test.txt');
    });
  });
})();
