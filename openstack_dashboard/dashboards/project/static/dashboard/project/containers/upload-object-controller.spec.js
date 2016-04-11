/**
 *    (c) Copyright 2016 Rackspace US, Inc
 *
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

(function() {
  'use strict';

  describe('horizon.dashboard.project.containers upload-object controller', function() {
    var controller, $scope;

    beforeEach(module('horizon.framework'));
    beforeEach(module('horizon.dashboard.project.containers'));

    beforeEach(module(function ($provide) {
      $provide.value('horizon.dashboard.project.containers.containers-model', {
        container: {name: 'spam'},
        folder: 'ham'
      });
    }));

    beforeEach(inject(function ($injector, _$rootScope_) {
      controller = $injector.get('$controller');
      $scope = _$rootScope_.$new(true);
    }));

    function createController() {
      return controller('UploadObjectModalController', {$scope: $scope});
    }

    it('should initialise the controller model when created', function test() {
      var ctrl = createController();
      expect(ctrl.model.name).toEqual('');
      expect(ctrl.model.container.name).toEqual('spam');
      expect(ctrl.model.folder).toEqual('ham');
    });

    it('should respond to file changes correctly', function test() {
      var ctrl = createController();
      spyOn($scope, '$digest');
      var file = {name: 'eggs'};

      ctrl.changeFile([file]);

      expect(ctrl.model.name).toEqual('eggs');
      expect(ctrl.model.upload_file).toEqual(file);
      expect($scope.$digest).toHaveBeenCalled();
    });

    it('should respond to file changes correctly if no files are present', function test() {
      var ctrl = createController();
      spyOn($scope, '$digest');

      ctrl.changeFile([]);

      expect(ctrl.model.name).toEqual('');
      expect($scope.$digest).not.toHaveBeenCalled();
    });
  });
})();
