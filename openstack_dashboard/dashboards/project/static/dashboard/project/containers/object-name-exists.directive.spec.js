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
    beforeEach(module('horizon.app.core.openstack-service-api'));
    beforeEach(module('horizon.dashboard.project.containers'));
    beforeEach(module('horizon.framework'));

    var $compile, $scope, model, element, swiftAPI, apiDeferred;

    beforeEach(inject(function inject($injector, _$q_, _$rootScope_) {
      $scope = _$rootScope_.$new();
      $compile = $injector.get('$compile');
      model = $injector.get('horizon.dashboard.project.containers.containers-model');
      swiftAPI = $injector.get('horizon.app.core.openstack-service-api.swift');
      apiDeferred = _$q_.defer();
      spyOn(swiftAPI, 'getObjectDetails').and.returnValue(apiDeferred.promise);
      model.container = {name: 'spam'};
      model.folder = 'ham';
      $scope.model = '';
      element = angular.element(
        '<div ng-form="form">' +
        '<input name="model" type="text" object-name-exists ng-model="model" />' +
        '<span ng-if="form.model.$error.exists">EXISTS</span>' +
        '</div>'
      );
      element = $compile(element)($scope);
      $scope.$apply();
    }));

    it('should reject names that exist', function test() {
      // edit the field
      element.find('input').val('exists.txt').trigger('input');
      expect(swiftAPI.getObjectDetails).toHaveBeenCalledWith('spam', 'ham/exists.txt', true);

      // cause the lookup to complete successfully (file exists)
      apiDeferred.resolve();
      $scope.$apply();

      expect(element.find('span').hasClass('ng-hide')).toEqual(false);
    });

    it('should accept names that do not exist', function test() {
      // edit the field
      element.find('input').val('not-exists.txt').trigger('input');
      expect(swiftAPI.getObjectDetails).toHaveBeenCalledWith('spam', 'ham/not-exists.txt', true);

      // cause the lookup to complete successfully (file exists)
      apiDeferred.resolve();
      $scope.$apply();
      expect(element.find('span').hasClass('ng-hide')).toEqual(false);
    });
  });
})();
