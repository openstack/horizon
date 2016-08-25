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

  describe('horizon.dashboard.project.containers objects controller', function() {
    beforeEach(module('horizon.framework'));
    beforeEach(module('horizon.app.core.openstack-service-api'));
    beforeEach(module('horizon.dashboard.project.containers'));
    beforeEach(module(function before($provide) {
      $routeParams = {};
      $provide.value('$routeParams', $routeParams);
      $provide.constant('horizon.dashboard.project.containers.basePath', '/base/path/');
      $provide.constant('horizon.dashboard.project.containers.containerRoute', 'eggs/');
    }));

    var $q, $scope, $routeParams, controller, model;

    beforeEach(inject(function inject($injector, _$q_, _$rootScope_) {
      controller = $injector.get('$controller');
      $q = _$q_;
      $scope = _$rootScope_.$new();
      model = $injector.get('horizon.dashboard.project.containers.containers-model');

      // we never really want this to happen for realsies below
      var deferred = $q.defer();
      deferred.resolve();
      spyOn(model, 'selectContainer').and.returnValue(deferred.promise);
    }));

    function createController(folder) {
      // this is embedding a bit of knowledge of model but on the other hand
      // we're not testing model in this file, so it's OK
      model.container = {name: 'spam'};
      $routeParams.container = 'spam';
      model.folder = $routeParams.folder = folder;
      return controller(
        'horizon.dashboard.project.containers.ObjectsController',
        {$scope: $scope}
      );
    }

    it('should load contents', function test () {
      var ctrl = createController();

      expect(ctrl.containerURL).toEqual('eggs/spam/');
      expect(ctrl.currentURL).toEqual('eggs/spam/');

      model.intialiseDeferred.resolve();
      $scope.$apply();

      expect(model.selectContainer).toHaveBeenCalledWith('spam', undefined);
    });

    it('should generate breadcrumb URLs', function test() {
      var ctrl = createController();
      model.pseudo_folder_hierarchy = ['foo', 'b#r'];
      expect(ctrl.getBreadcrumbs()).toEqual([
        {label: 'foo', url: 'eggs/spam/foo'},
        {label: 'b#r', url: 'eggs/spam/foo/b%23r'}
      ]);
    });

    it('should generate object URLs', function test() {
      var ctrl = createController();
      expect(ctrl.objectURL({name: 'b#r'})).toEqual('eggs/spam/b%23r');
    });

    it('should handle subfolders', function test() {
      var ctrl = createController('ham');

      expect(ctrl.containerURL).toEqual('eggs/spam/');
      expect(ctrl.currentURL).toEqual('eggs/spam/ham/');

      model.intialiseDeferred.resolve();
      $scope.$apply();

      expect(model.selectContainer).toHaveBeenCalledWith('spam', 'ham');
    });

    it('should handle action results when result is undefined', function test() {
      var ctrl = createController();

      spyOn(model, 'updateContainer');
      spyOn($scope, '$broadcast');
      ctrl.actionResultHandler();

      expect($scope.$broadcast).not.toHaveBeenCalled();
      expect(model.updateContainer).not.toHaveBeenCalled();
      expect(model.selectContainer).not.toHaveBeenCalled();
    });

    it('should handle action results with an empty deleted list', function test() {
      var ctrl = createController();
      var result = { deleted: [] };

      spyOn(model, 'updateContainer');
      spyOn($scope, '$broadcast');
      ctrl.actionResultHandler(result);

      expect($scope.$broadcast).not.toHaveBeenCalled();
      expect(model.updateContainer).not.toHaveBeenCalled();
      expect(model.selectContainer).not.toHaveBeenCalled();
    });

    it('should handle action results', function test() {
      var ctrl = createController();
      spyOn($scope, '$broadcast');
      spyOn(model, 'updateContainer');

      var d = $q.defer();
      ctrl.actionResultHandler(d.promise);
      d.resolve({deleted: [1]});
      $scope.$apply();

      expect(model.updateContainer).toHaveBeenCalled();
      expect(model.selectContainer).toHaveBeenCalledWith('spam', undefined);
    });
  });
})();
