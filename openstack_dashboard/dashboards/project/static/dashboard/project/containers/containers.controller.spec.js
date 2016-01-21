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

  describe('horizon.dashboard.project.containers containers controller', function() {
    beforeEach(module('horizon.app.core.openstack-service-api'));
    beforeEach(module('horizon.framework'));
    beforeEach(module('horizon.dashboard.project'));

    var fakeModel = {
      loadContainerContents: angular.noop,
      initialize: angular.noop,
      fetchContainerDetail: function fake() {
        return {
          then: function then(callback) {
            callback({
              name: 'spam',
              is_public: true
            });
          }
        };
      }
    };

    var $q, $modal, $location, $rootScope, controller, simpleModal, swiftAPI, toast;

    beforeEach(module('horizon.dashboard.project.containers', function($provide) {
      $provide.value('horizon.dashboard.project.containers.containers-model', fakeModel);
    }));

    beforeEach(inject(function ($injector, _$q_, _$modal_, _$rootScope_) {
      controller = $injector.get('$controller');
      $q = _$q_;
      $location = $injector.get('$location');
      $modal = _$modal_;
      $rootScope = _$rootScope_;
      simpleModal = $injector.get('horizon.framework.widgets.modal.simple-modal.service');
      swiftAPI = $injector.get('horizon.app.core.openstack-service-api.swift');
      toast = $injector.get('horizon.framework.widgets.toast.service');

      spyOn(fakeModel, 'initialize');
      spyOn(fakeModel, 'loadContainerContents');
      spyOn(fakeModel, 'fetchContainerDetail').and.callThrough();
      spyOn(toast, 'add');
    }));

    function createController() {
      return controller(
        'horizon.dashboard.project.containers.ContainersController', {
          'horizon.dashboard.project.containers.baseRoute': 'base ham',
          'horizon.dashboard.project.containers.containerRoute': 'eggs '
        });
    }

    it('should set containerRoute', function() {
      var ctrl = createController();
      expect(ctrl.containerRoute).toBeDefined();
    });

    it('should invoke initialise the model when created', function() {
      createController();
      expect(fakeModel.initialize).toHaveBeenCalled();
    });

    it('should update current container name when one is selected', function () {
      spyOn($location, 'path');
      var ctrl = createController();
      ctrl.selectContainer({name: 'and spam'});
      expect($location.path).toHaveBeenCalledWith('eggs and spam');
      expect(ctrl.model.container.name).toEqual('and spam');
      expect(fakeModel.fetchContainerDetail).toHaveBeenCalledWith({name: 'and spam'});
    });

    it('should set container to public', function test() {
      var deferred = $q.defer();
      spyOn(swiftAPI, 'setContainerAccess').and.returnValue(deferred.promise);
      var ctrl = createController();

      var container = {name: 'spam', is_public: true};
      ctrl.toggleAccess(container);

      expect(swiftAPI.setContainerAccess).toHaveBeenCalledWith('spam', true);

      deferred.resolve();
      $rootScope.$apply();
      expect(toast.add).toHaveBeenCalledWith('success', 'Container spam is now public.');
      expect(fakeModel.fetchContainerDetail).toHaveBeenCalledWith(container, true);
    });

    it('should set container to private', function test() {
      var deferred = $q.defer();
      spyOn(swiftAPI, 'setContainerAccess').and.returnValue(deferred.promise);
      var ctrl = createController();

      var container = {name: 'spam', is_public: false};
      ctrl.toggleAccess(container);

      expect(swiftAPI.setContainerAccess).toHaveBeenCalledWith('spam', false);

      deferred.resolve();
      $rootScope.$apply();
      expect(toast.add).toHaveBeenCalledWith('success', 'Container spam is now private.');
      expect(fakeModel.fetchContainerDetail).toHaveBeenCalledWith(container, true);
    });

    it('should open a dialog for delete confirmation', function test() {
      // fake promise to poke at later
      var deferred = $q.defer();
      var result = { result: deferred.promise };
      spyOn(simpleModal, 'modal').and.returnValue(result);

      var ctrl = createController();
      spyOn(ctrl, 'deleteContainerAction');

      ctrl.deleteContainer({name: 'spam', is_public: true});

      // ensure modal is constructed correctly.
      expect(simpleModal.modal).toHaveBeenCalled();
      var spec = simpleModal.modal.calls.mostRecent().args[0];
      expect(spec.title).toBeDefined();
      expect(spec.body).toBeDefined();
      expect(spec.submit).toBeDefined();
      expect(spec.cancel).toBeDefined();

      // when the modal is resolved, make sure delete is called
      deferred.resolve();
      $rootScope.$apply();
      expect(ctrl.deleteContainerAction).toHaveBeenCalledWith({name: 'spam', is_public: true});
    });

    it('should delete containers', function test() {
      fakeModel.containers = [{name: 'one'}, {name: 'two'}, {name: 'three'}];
      var deferred = $q.defer();
      spyOn(swiftAPI, 'deleteContainer').and.returnValue(deferred.promise);
      spyOn($location, 'path');

      var ctrl = createController();
      ctrl.model.container = {name: 'one'};
      createController().deleteContainerAction(fakeModel.containers[1]);

      deferred.resolve();
      $rootScope.$apply();
      expect(toast.add).toHaveBeenCalledWith('success', 'Container two deleted.');

      expect(fakeModel.containers[0].name).toEqual('one');
      expect(fakeModel.containers[1].name).toEqual('three');
      expect(fakeModel.containers.length).toEqual(2);
      expect($location.path).not.toHaveBeenCalled();
    });

    it('should reset the location when the current container is deleted', function test() {
      fakeModel.containers = [{name: 'one'}, {name: 'two'}, {name: 'three'}];
      var deferred = $q.defer();
      spyOn(swiftAPI, 'deleteContainer').and.returnValue(deferred.promise);
      spyOn($location, 'path');

      var ctrl = createController();
      ctrl.model.container = {name: 'two'};
      ctrl.deleteContainerAction(fakeModel.containers[1]);

      deferred.resolve();
      $rootScope.$apply();
      expect($location.path).toHaveBeenCalledWith('base ham');
    });

    it('should open a dialog for creation', function test() {
      var deferred = $q.defer();
      var result = { result: deferred.promise };
      spyOn($modal, 'open').and.returnValue(result);

      var ctrl = createController();
      spyOn(ctrl, 'createContainerAction');

      ctrl.createContainer();

      expect($modal.open).toHaveBeenCalled();
      var spec = $modal.open.calls.mostRecent().args[0];
      expect(spec.backdrop).toBeDefined();
      expect(spec.controller).toEqual('CreateContainerModalController as ctrl');
      expect(spec.templateUrl).toBeDefined();

      // when the modal is resolved, make sure delete is called
      deferred.resolve('spam');
      $rootScope.$apply();
      expect(ctrl.createContainerAction).toHaveBeenCalledWith('spam');
    });

    it('should create containers', function test() {
      fakeModel.containers = [];
      var deferred = $q.defer();
      spyOn(swiftAPI, 'createContainer').and.returnValue(deferred.promise);

      createController().createContainerAction({name: 'spam', public: true});

      deferred.resolve();
      $rootScope.$apply();
      expect(toast.add).toHaveBeenCalledWith('success', 'Container spam created.');
      expect(fakeModel.containers[0].name).toEqual('spam');
      expect(fakeModel.containers.length).toEqual(1);
    });
  });
})();
