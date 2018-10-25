/**
 * Licensed under the Apache License, Version 2.0 (the "License"); you may
 * not use self file except in compliance with the License. You may obtain
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
(function() {
  'use strict';

  describe('delete-image-selected component', function() {
    var $scope, $element, $controller, $q;
    // Mock image data
    var mockAllowed = { allowed: true };
    var mockDisallowed = { allowed: false };

    beforeEach(module('templates'));
    beforeEach(module('horizon.app.core.images.actions', function($provide) {
      // Injects a mock 'action' directive for unit testing
      $provide.decorator('actionDirective', function($delegate) {
        var component = $delegate[0];

        component.template = '<div>Mock</div>';
        component.templateUrl = null;

        return $delegate;
      });

      // Mock delete-image.service. The disabling mechanism uses the allowed
      // function from that service using the promises API, which is mocked
      // here.
      $provide.service(
        'horizon.app.core.images.actions.delete-image.service', function() {
          return {
            allowed: function(mockImage) {
              var deferred = $q.defer();
              if (mockImage.allowed) {
                deferred.resolve();
              } else {
                deferred.reject();
              }
              return deferred.promise;
            }
          };
        }
      );
    }));
    beforeEach(inject(function(_$rootScope_, _$compile_, _$q_) {
      $q = _$q_;
      $scope = _$rootScope_.$new();
      var tag = angular.element(
        '<delete-image-selected selected="selected" callback="callback">' +
        '</delete-image-selected>'
      );

      $scope.selected = [];

      $element = _$compile_(tag)($scope);
      $scope.$apply();

      $controller = $element.controller('deleteImageSelected');
    }));

    it('disables for empty list', function() {
      expect($controller.disabled).toBe(true);
    });

    it('enables for all allowed images', function() {
      // Selections change the object; just pushing in new values wouldn't
      // trigger disable recalculations
      $scope.selected = [$.extend({}, mockAllowed)];
      $scope.$apply();
      expect($controller.disabled).toBe(false);
    });

    it('disables for all disallowed images', function() {
      $scope.selected = [$.extend({}, mockDisallowed)];
      $scope.$apply();
      expect($controller.disabled).toBe(true);
    });

    it('disables for mixed images', function() {
      $scope.selected = [
        $.extend({}, mockDisallowed),
        $.extend({}, mockDisallowed)
      ];
      $scope.$apply();
      expect($controller.disabled).toBe(true);
    });
  });
})();
