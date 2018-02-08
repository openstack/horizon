/**
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

  describe('horizon.dashboard.project.containers check-copy-destination.directive', function() {
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
      spyOn(swiftAPI, 'getContainer').and.returnValue(apiDeferred.promise);
      spyOn(swiftAPI, 'getObjectDetails').and.returnValue(apiDeferred.promise);
      model.container = {name: 'spam'};
      model.folder = 'ham';

      $scope.ctrl = {
        model: {
          dest_container: '',
          dest_name: ''
        }
      };

      element = angular.element(
        '<div ng-form="copyForm">' +
        '<input id="id_dest_container" name="dest_container" type="text" ' +
        'check-copy-destination ng-model="ctrl.model.dest_container" />' +
        '<span id="id_span_dest_container" ' +
        'ng-show="copyForm.dest_container.$error.containerNotFound">' +
        'Container does not exist</span>' +
        '' +
        '<input id="id_dest_name" name="dest_name" type="text"' +
        ' check-copy-destination ng-model="ctrl.model.dest_name" />' +
        '<span id="id_span_dest_name" ' +
        'ng-show="copyForm.dest_name.$error.objectExists">' +
        'Object already exists</span>' +
        '</div>'
      );
      element = $compile(element)($scope);
      $scope.$apply();
    }));

    it('should accept container name that exists', function test() {
      // input field value
      var containerName = 'someContainerName';
      element.find('input#id_dest_container').val(containerName).trigger('input');
      expect(swiftAPI.getContainer).toHaveBeenCalledWith(containerName, true);

      // In case resolve() returned, it means specified container
      // correctly exists. so error <span> for container should not be displayed.
      apiDeferred.resolve();
      $scope.$apply();
      expect(element.find('#id_span_dest_container').hasClass('ng-hide')).toEqual(true);
    });

    it('should accept container name that dees not exist', function test() {
      // input field value
      var containerName = 'someContainerName';
      element.find('input#id_dest_container').val(containerName).trigger('input');
      expect(swiftAPI.getContainer).toHaveBeenCalledWith(containerName, true);

      // In case reject() returned, it means specified container
      // does not exist. so error <span> for container should be displayed.
      apiDeferred.reject();
      $scope.$apply();
      expect(element.find('#id_span_dest_container').hasClass('ng-hide')).toEqual(false);
    });

    it('should not accept object already exists to prevent overwrite of object', function test() {
      // input field value (destination container)
      var containerName = 'someContainerName';
      element.find('input#id_dest_container').val(containerName).trigger('input');
      expect(swiftAPI.getContainer).toHaveBeenCalledWith(containerName, true);

      // In case resolve() returned, it means specified container
      // correctly exists. so error <span> for container should not be displayed.
      apiDeferred.resolve();
      $scope.$apply();

      // input field value (destination object)
      var objectName = 'someObjectName';
      element.find('input#id_dest_name').val(objectName).trigger('input');
      expect(swiftAPI.getObjectDetails).toHaveBeenCalledWith(containerName, objectName, true);

      apiDeferred.resolve();
      $scope.$apply();

      // In case resolve() returned, it means specified object
      // already exists. so error <span> for object should be displayed.
      expect(element.find('#id_span_dest_name').hasClass('ng-hide')).toEqual(false);
    });

    it('should accept object name does not exist', function test() {
      // input field value (destination container)
      var containerName = 'someContainerName';
      element.find('input#id_dest_container').val(containerName).trigger('input');
      expect(swiftAPI.getContainer).toHaveBeenCalledWith(containerName, true);

      // In case resolve() returned, it means specified container
      // correctly exists. so error <span> for container should not be displayed.
      apiDeferred.resolve();
      $scope.$apply();

      // input field value (destination object)
      var objectName = 'someObjectName';
      element.find('input#id_dest_name').val(objectName).trigger('input');
      expect(swiftAPI.getObjectDetails).toHaveBeenCalledWith(containerName, objectName, true);

      apiDeferred.reject();
      $scope.$apply();

      // In case resolve() returned, it means specified object
      // already exists. so error <span> for object should be displayed.
      expect(element.find('#id_span_dest_name').hasClass('ng-hide')).toEqual(false);
    });
  });
})();
