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

    var $modal, $q, $scope, $routeParams, controller, modalWaitSpinnerService, model,
      swiftAPI, toast;

    beforeEach(inject(function inject($injector, _$q_, _$rootScope_) {
      controller = $injector.get('$controller');
      $modal = $injector.get('$modal');
      $q = _$q_;
      $scope = _$rootScope_.$new();
      modalWaitSpinnerService = $injector.get(
        'horizon.framework.widgets.modal-wait-spinner.service'
      );
      model = $injector.get('horizon.dashboard.project.containers.containers-model');
      swiftAPI = $injector.get('horizon.app.core.openstack-service-api.swift');
      toast = $injector.get('horizon.framework.widgets.toast.service');

      // we never really want this to happen for realsies below
      var deferred = $q.defer();
      deferred.resolve();
      spyOn(model, 'selectContainer').and.returnValue(deferred.promise);

      // common spies
      spyOn(modalWaitSpinnerService, 'showModalSpinner');
      spyOn(modalWaitSpinnerService, 'hideModalSpinner');
      spyOn(toast, 'add');
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

    it('should determine "any" selectability', function test() {
      var ctrl = createController();
      ctrl.model.objects = [{}, {}];

      expect(ctrl.anySelectable()).toEqual(true);
    });

    it('should determine "any" selectability with none', function test() {
      var ctrl = createController();
      ctrl.model.objects = [];

      expect(ctrl.anySelectable()).toEqual(false);
    });

    it('should determine whether files are selected if none selected', function test() {
      var ctrl = createController();
      ctrl.selected = {};
      expect(ctrl.isSelected({name: 'one'})).toEqual(false);
    });

    it('should determine whether files are selected if others selected', function test() {
      var ctrl = createController();
      ctrl.selected = {two: {checked: true}};
      expect(ctrl.isSelected({name: 'one'})).toEqual(false);
    });

    it('should determine whether files are selected if selected', function test() {
      var ctrl = createController();
      ctrl.selected = {one: {checked: true}};
      expect(ctrl.isSelected({name: 'one'})).toEqual(true);
    });

    it('should determine whether files are selected if not selected', function test() {
      var ctrl = createController();
      ctrl.selected = {one: {checked: false}};
      expect(ctrl.isSelected({name: 'one'})).toEqual(false);
    });

    it('should toggle selected state on', function test() {
      var ctrl = createController();
      ctrl.selected = {};
      ctrl.numSelected = 0;
      ctrl.toggleSelect({name: 'one'});
      expect(ctrl.selected.one.checked).toEqual(true);
      expect(ctrl.numSelected).toEqual(1);
    });

    it('should toggle selected state off', function test() {
      var ctrl = createController();
      ctrl.selected = {one: {checked: true}};
      ctrl.numSelected = 1;
      ctrl.toggleSelect({name: 'one'});
      expect(ctrl.selected.one.checked).toEqual(false);
      expect(ctrl.numSelected).toEqual(0);
    });

    it('should select all', function test() {
      var ctrl = createController();
      spyOn(ctrl, 'clearSelected').and.callThrough();
      ctrl.selected = {some: 'stuff'};
      ctrl.numSelected = 1;
      ctrl.model.objects = [
        {name: 'one'},
        {name: 'two'}
      ];
      ctrl.selectAll();
      expect(ctrl.clearSelected).toHaveBeenCalled();
      expect(ctrl.selected).toEqual({
        one: {checked: true, file: {name: 'one'}},
        two: {checked: true, file: {name: 'two'}}
      });
      expect(ctrl.numSelected).toEqual(2);
    });

    it('should confirm bulk deletion with a modal', function test() {
      // deferred to be resolved then the modal is "closed" in a bit
      var deferred = $q.defer();
      var result = { result: deferred.promise };
      spyOn($modal, 'open').and.returnValue(result);

      var ctrl = createController();
      spyOn(ctrl, 'clearSelected');
      spyOn(model, 'updateContainer');

      ctrl.model.objects = [{name: 'one'}, {name: 'two'}, {name: 'three'}];
      ctrl.selected = {
        one: {file: {name: 'one'}, checked: false},
        two: {file: {name: 'two'}, checked: true}
      };
      ctrl.numSelected = 1;

      ctrl.deleteSelected();

      expect($modal.open).toHaveBeenCalled();
      var spec = $modal.open.calls.mostRecent().args[0];
      expect(spec.controller).toBeDefined();
      expect(spec.templateUrl).toBeDefined();
      expect(spec.resolve).toBeDefined();
      expect(spec.resolve.selected).toBeDefined();
      expect(spec.resolve.selected()).toEqual(ctrl.selected);

      // "close" the modal, make sure delete is called
      deferred.resolve();
      $scope.$apply();
      expect(ctrl.clearSelected).toHaveBeenCalled();
      expect(model.updateContainer).toHaveBeenCalled();

      // selectec objects should have been removed
      expect(ctrl.model.objects.length).toEqual(2);
    });

    it('should create "create folder" modals', function test() {
      var deferred = $q.defer();
      var result = { result: deferred.promise };
      spyOn($modal, 'open').and.returnValue(result);

      var ctrl = createController();
      spyOn(ctrl, 'createFolderCallback');
      ctrl.createFolder();

      expect($modal.open).toHaveBeenCalled();
      var spec = $modal.open.calls.mostRecent().args[0];
      expect(spec.backdrop).toBeDefined();
      expect(spec.controller).toBeDefined();
      expect(spec.templateUrl).toEqual('/base/path/create-folder-modal.html');

      deferred.resolve('new-folder');
      $scope.$apply();
      expect(ctrl.createFolderCallback).toHaveBeenCalledWith('new-folder');
    });

    it('should create folders', function test() {
      var deferred = $q.defer();
      spyOn(swiftAPI, 'createFolder').and.returnValue(deferred.promise);
      spyOn(model, 'updateContainer');

      var ctrl = createController('ham');
      ctrl.createFolderCallback('new-folder');

      expect(swiftAPI.createFolder).toHaveBeenCalledWith('spam', 'ham/new-folder');

      deferred.resolve();
      $scope.$apply();
      expect(toast.add).toHaveBeenCalledWith('success', 'Folder new-folder created.');
      expect(model.selectContainer).toHaveBeenCalledWith('spam', 'ham');
      expect(model.updateContainer).toHaveBeenCalled();
    });

    it('should create "upload file" modals', function test() {
      var deferred = $q.defer();
      var result = { result: deferred.promise };
      spyOn($modal, 'open').and.returnValue(result);

      var ctrl = createController();
      spyOn(ctrl, 'uploadObjectCallback');
      ctrl.uploadObject();

      expect($modal.open).toHaveBeenCalled();
      var spec = $modal.open.calls.mostRecent().args[0];
      expect(spec.backdrop).toBeDefined();
      expect(spec.controller).toBeDefined();
      expect(spec.templateUrl).toEqual('/base/path/upload-object-modal.html');

      deferred.resolve('new-file');
      $scope.$apply();
      expect(ctrl.uploadObjectCallback).toHaveBeenCalledWith('new-file');
    });

    it('should upload files', function test() {
      // uploadObjectCallback is quite complex, so we have a bit to mock out
      var deferred = $q.defer();
      spyOn(swiftAPI, 'uploadObject').and.returnValue(deferred.promise);
      spyOn(model, 'updateContainer');

      var ctrl = createController('ham');
      ctrl.uploadObjectCallback({upload_file: 'file', name: 'eggs.txt'});
      expect(modalWaitSpinnerService.showModalSpinner).toHaveBeenCalled();

      expect(swiftAPI.uploadObject).toHaveBeenCalledWith(
        'spam', 'ham/eggs.txt', 'file'
      );

      // the swift API returned
      deferred.resolve();
      $scope.$apply();
      expect(toast.add).toHaveBeenCalledWith('success', 'File eggs.txt uploaded.');
      expect(model.selectContainer).toHaveBeenCalledWith('spam', 'ham');
      expect(modalWaitSpinnerService.hideModalSpinner).toHaveBeenCalled();
      expect(model.updateContainer).toHaveBeenCalled();
    });

    it('should clear the spinner on file upload error', function test() {
      // uploadObjectCallback is quite complex, so we have a bit to mock out
      var deferred = $q.defer();
      spyOn(swiftAPI, 'uploadObject').and.returnValue(deferred.promise);
      spyOn(model, 'updateContainer');

      var ctrl = createController('ham');
      ctrl.uploadObjectCallback({upload_file: 'file', name: 'eggs.txt'});
      expect(modalWaitSpinnerService.showModalSpinner).toHaveBeenCalled();

      expect(swiftAPI.uploadObject).toHaveBeenCalledWith(
        'spam', 'ham/eggs.txt', 'file'
      );

      // HERE is the difference from the previous test
      deferred.reject();
      $scope.$apply();
      expect(modalWaitSpinnerService.hideModalSpinner).toHaveBeenCalled();
      expect(model.updateContainer).not.toHaveBeenCalled();
    });

  });
})();
