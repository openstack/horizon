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

  describe('horizon.dashboard.project.containers objects batch actions', function test() {
    beforeEach(module('horizon.app.core.openstack-service-api'));
    beforeEach(module('horizon.framework'));
    beforeEach(module('horizon.dashboard.project'));

    var $window = {location: {href: 'ham'}};

    beforeEach(module(function before($provide) {
      $provide.constant('horizon.dashboard.project.containers.basePath', '/base/path/');
      $provide.value('$window', $window);
    }));

    var batchActions, modalWaitSpinnerService, model, $q, $rootScope, swiftAPI, toast;

    beforeEach(inject(function inject($injector, _$q_, _$rootScope_) {
      var resourceService = $injector.get('horizon.framework.conf.resource-type-registry.service');
      var objectResCode = $injector.get('horizon.dashboard.project.containers.object.resourceType');
      batchActions = resourceService.getResourceType(objectResCode).batchActions;
      modalWaitSpinnerService = $injector.get(
        'horizon.framework.widgets.modal-wait-spinner.service'
      );
      model = $injector.get('horizon.dashboard.project.containers.containers-model');
      $q = _$q_;
      $rootScope = _$rootScope_;
      swiftAPI = $injector.get('horizon.app.core.openstack-service-api.swift');
      toast = $injector.get('horizon.framework.widgets.toast.service');

      // we never really want this to happen for realsies below
      var deferred = $q.defer();
      deferred.resolve();
      spyOn(model, 'selectContainer').and.returnValue(deferred.promise);

      // common spies
      spyOn(model, 'updateContainer');
      spyOn(modalWaitSpinnerService, 'showModalSpinner');
      spyOn(modalWaitSpinnerService, 'hideModalSpinner');
      spyOn(toast, 'add');
    }));

    it('should create an actions list', function test() {
      expect(batchActions.length).toEqual(3);
      angular.forEach(batchActions, function check(action) {
        expect(action.service).toBeDefined();
        expect(action.template).toBeDefined();
        expect(action.template.text).toBeDefined();
      });
    });

    describe('uploadService', function test() {
      var $uibModal, uploadService;

      beforeEach(inject(function inject($injector, _$uibModal_) {
        $uibModal = _$uibModal_;
        uploadService = $injector.get(
          'horizon.dashboard.project.containers.objects-batch-actions.upload'
        );
      }));

      it('should have an allowed and perform', function test() {
        expect(uploadService.allowed).toBeDefined();
        expect(uploadService.perform).toBeDefined();
      });

      it('should allow upload', function test() {
        expectAllowed(uploadService.allowed());
      });

      it('should create "upload file" modals', function test() {
        var deferred = $q.defer();
        var result = { result: deferred.promise };
        spyOn($uibModal, 'open').and.returnValue(result);
        model.container = {name: 'ham'};

        spyOn(uploadService, 'uploadObjectCallback');
        uploadService.perform();

        expect($uibModal.open).toHaveBeenCalled();
        var spec = $uibModal.open.calls.mostRecent().args[0];
        expect(spec.backdrop).toBeDefined();
        expect(spec.controller).toBeDefined();
        expect(spec.templateUrl).toEqual('/base/path/upload-object-modal.html');

        deferred.resolve('new-file');
        $rootScope.$apply();
        expect(uploadService.uploadObjectCallback).toHaveBeenCalledWith('new-file');
      });

      it('should upload files', function test() {
        // uploadObjectCallback is quite complex, so we have a bit to mock out
        var deferred = $q.defer();
        spyOn(swiftAPI, 'uploadObject').and.returnValue(deferred.promise);
        model.container = {name: 'spam'};
        model.folder = 'ham';

        uploadService.uploadObjectCallback({upload_file: 'file', name: 'eggs.txt'});
        expect(modalWaitSpinnerService.showModalSpinner).toHaveBeenCalled();

        expect(swiftAPI.uploadObject).toHaveBeenCalledWith(
          'spam', 'ham/eggs.txt', 'file'
        );

        // the swift API returned
        deferred.resolve();
        $rootScope.$apply();
        expect(toast.add).toHaveBeenCalledWith('success', 'File eggs.txt uploaded.');
        expect(model.selectContainer).toHaveBeenCalledWith('spam', 'ham');
        expect(modalWaitSpinnerService.hideModalSpinner).toHaveBeenCalled();
        expect(model.updateContainer).toHaveBeenCalled();
      });

    });

    describe('createFolderService', function test() {
      var $uibModal, createFolderService;

      beforeEach(inject(function inject($injector, _$uibModal_) {
        $uibModal = _$uibModal_;
        createFolderService = $injector.get(
          'horizon.dashboard.project.containers.objects-batch-actions.create-folder'
        );
      }));

      it('should have an allowed and perform', function test() {
        expect(createFolderService.allowed).toBeDefined();
        expect(createFolderService.perform).toBeDefined();
      });

      it('should allow upload', function test() {
        expectAllowed(createFolderService.allowed());
      });

      it('should create "create folder" modals', function test() {
        var deferred = $q.defer();
        var result = {result: deferred.promise};
        spyOn($uibModal, 'open').and.returnValue(result);

        spyOn(createFolderService, 'createFolderCallback');
        createFolderService.perform();

        expect($uibModal.open).toHaveBeenCalled();
        var spec = $uibModal.open.calls.mostRecent().args[0];
        expect(spec.backdrop).toBeDefined();
        expect(spec.controller).toBeDefined();
        expect(spec.templateUrl).toEqual('/base/path/create-folder-modal.html');

        deferred.resolve('new-folder');
        $rootScope.$apply();
        expect(createFolderService.createFolderCallback).toHaveBeenCalledWith('new-folder');
      });

      it('should create folders', function test() {
        var deferred = $q.defer();
        spyOn(swiftAPI, 'createFolder').and.returnValue(deferred.promise);
        model.container = {name: 'spam'};
        model.folder = 'ham';

        createFolderService.createFolderCallback('new-folder');

        expect(swiftAPI.createFolder).toHaveBeenCalledWith('spam', 'ham/new-folder');

        deferred.resolve();
        $rootScope.$apply();
        expect(toast.add).toHaveBeenCalledWith('success', 'Folder new-folder created.');
        expect(model.selectContainer).toHaveBeenCalledWith('spam', 'ham');
        expect(model.updateContainer).toHaveBeenCalled();
      });
    });

    describe('deleteService', function test() {
      var actionResultService, deleteService, $uibModal, $q;

      beforeEach(inject(function inject($injector, _$q_, _$uibModal_) {
        actionResultService = $injector.get('horizon.framework.util.actions.action-result.service');
        deleteService = $injector.get(
          'horizon.dashboard.project.containers.objects-batch-actions.delete'
        );
        $uibModal = _$uibModal_;
        $q = _$q_;
      }));

      it('should have an allowed and perform', function test() {
        expect(deleteService.allowed).toBeDefined();
        expect(deleteService.perform).toBeDefined();
      });

      it('should always allow', function test() {
        expectAllowed(deleteService.allowed());
      });

      it('should confirm bulk deletion with a modal', function test() {
        // deferred to be resolved then the modal is "closed" in a bit
        var deferred = $q.defer();
        var result = {result: deferred.promise};
        spyOn($uibModal, 'open').and.returnValue(result);
        spyOn(actionResultService, 'getActionResult').and.callThrough();

        deleteService.perform(['one', 'two']);

        expect($uibModal.open).toHaveBeenCalled();
        var spec = $uibModal.open.calls.mostRecent().args[0];
        expect(spec.backdrop).toBeDefined();
        expect(spec.controller).toEqual('DeleteObjectsModalController as ctrl');
        expect(spec.templateUrl).toEqual('/base/path/delete-objects-modal.html');

        // "close" the modal, make sure delete is called
        deferred.resolve();
        $rootScope.$apply();
        expect(actionResultService.getActionResult).toHaveBeenCalled();
      });
    });

    function exerciseAllowedPromise(promise) {
      var handler = jasmine.createSpyObj('handler', ['success', 'error']);
      promise.then(handler.success, handler.error);
      $rootScope.$apply();
      return handler;
    }

    function expectAllowed(promise) {
      var handler = exerciseAllowedPromise(promise);
      expect(handler.success).toHaveBeenCalled();
      expect(handler.error).not.toHaveBeenCalled();
    }

  });
})();
