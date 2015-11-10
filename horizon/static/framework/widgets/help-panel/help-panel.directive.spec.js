/*
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

  describe('help-panel directive', function () {
    var $compile,
      $scope,
      element;

    beforeEach(module('templates'));
    beforeEach(module('horizon.framework'));
    beforeEach(inject(function ($injector) {
      $scope = $injector.get('$rootScope').$new();
      $compile = $injector.get('$compile');
      element = $compile('<help-panel>Help</help-panel>')($scope);
      $scope.$apply();
    }));

    it('should be compiled', function () {
      expect(element.html().trim()).not.toBe('Help');
      expect(element.text().trim()).toBe('Help');
    });

    it('should be closed by default', function () {
      expect(element[0].querySelector('.help-panel').className).toBe('help-panel');
    });

    it('should add "open" to class name if $scope.openHelp is true', function () {
      $scope.openHelp = true;
      $scope.$apply();
      expect(element[0].querySelector('.help-panel').className).toBe('help-panel open');
    });

    it('should remove "open" from class name if $scope.openHelp is false', function () {
      $scope.openHelp = true;
      $scope.$apply();
      $scope.openHelp = false;
      $scope.$apply();
      expect(element[0].querySelector('.help-panel').className).toBe('help-panel');
    });
  });

})();
