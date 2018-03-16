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

  describe('horizon.dashboard.project.containers objects row actions', function test() {
    beforeEach(module('horizon.app.core.openstack-service-api'));
    beforeEach(module('horizon.framework'));
    beforeEach(module('horizon.dashboard.project'));

    var $window = {location: {href: 'ham'}};

    beforeEach(module(function before($provide) {
      $provide.constant('horizon.dashboard.project.containers.basePath', '/base/path/');
      $provide.value('$window', $window);
    }));

    var rowActions, $uibModal, $rootScope, model;

    beforeEach(inject(function inject($injector, _$uibModal_, _$rootScope_) {
      var resourceService = $injector.get('horizon.framework.conf.resource-type-registry.service');
      var objectResCode = $injector.get('horizon.dashboard.project.containers.object.resourceType');
      rowActions = resourceService.getResourceType(objectResCode).itemActions;
      model = $injector.get('horizon.dashboard.project.containers.containers-model');
      $uibModal = _$uibModal_;
      $rootScope = _$rootScope_;
    }));

    it('should create an actions list', function test() {
      expect(rowActions.length).toEqual(5);
      angular.forEach(rowActions, function check(action) {
        expect(action.service).toBeDefined();
        expect(action.template).toBeDefined();
        expect(action.template.text).toBeDefined();
      });
    });

    describe('downloadService', function test() {
      var downloadService;

      beforeEach(inject(function inject($injector) {
        downloadService = $injector.get(
          'horizon.dashboard.project.containers.objects-actions.download'
        );
      }));

      it('should have an allowed and perform', function test() {
        expect(downloadService.allowed).toBeDefined();
        expect(downloadService.perform).toBeDefined();
      });

      it('should only allow files', function test() {
        expectAllowed(downloadService.allowed({is_object: true}));
      });

      it('should only now allow folders', function test() {
        expectNotAllowed(downloadService.allowed({is_object: false}));
      });

      it('should immediately return a URL from perform()', function test() {
        downloadService.perform({url: '/spam'});
        expect($window.location.href).toEqual('spam');
      });
    });

    describe('viewService', function test() {
      var swiftAPI, viewService, $q;

      beforeEach(inject(function inject($injector, _$q_) {
        swiftAPI = $injector.get('horizon.app.core.openstack-service-api.swift');
        viewService = $injector.get('horizon.dashboard.project.containers.objects-actions.view');
        $q = _$q_;
      }));

      it('should have an allowed and perform', function test() {
        expect(viewService.allowed).toBeDefined();
        expect(viewService.perform).toBeDefined();
      });

      it('should only allow files', function test() {
        expectAllowed(viewService.allowed({is_object: true}));
      });

      it('should only now allow folders', function test() {
        expectNotAllowed(viewService.allowed({is_object: false}));
      });

      it('should open a dialog on perform()', function test() {
        spyOn($uibModal, 'open');
        var deferred = $q.defer();
        spyOn(swiftAPI, 'getObjectDetails').and.returnValue(deferred.promise);
        model.container = {name: 'spam'};

        viewService.perform({name: 'ham'});

        deferred.resolve({data: {
          name: 'name',
          hash: 'hash',
          content_type: 'content/type',
          timestamp: 'timestamp',
          last_modified: 'last_modified',
          bytes: 'bytes'
        }});
        $rootScope.$apply();

        expect($uibModal.open).toHaveBeenCalled();
        var spec = $uibModal.open.calls.mostRecent().args[0];
        expect(spec.backdrop).toBeDefined();
        expect(spec.controller).toBeDefined();
        expect(spec.templateUrl).toEqual('/base/path/object-details-modal.html');
        expect(swiftAPI.getObjectDetails).toHaveBeenCalledWith('spam', 'ham');
      });
    });

    describe('deleteService', function test() {
      var actionResultService, deleteService, $q;

      beforeEach(inject(function inject($injector, _$q_) {
        actionResultService = $injector.get('horizon.framework.util.actions.action-result.service');
        deleteService = $injector.get(
          'horizon.dashboard.project.containers.objects-actions.delete'
        );
        $q = _$q_;
      }));

      it('should have an allowed and perform', function test() {
        expect(deleteService.allowed).toBeDefined();
        expect(deleteService.perform).toBeDefined();
      });

      it('should always allow', function test() {
        expectAllowed(deleteService.allowed());
      });

      it('should open a dialog on perform()', function test() {
        // deferred to be resolved then the modal is "closed" in a bit
        var deferred = $q.defer();
        var result = { result: deferred.promise };
        spyOn($uibModal, 'open').and.returnValue(result);
        spyOn(actionResultService, 'getActionResult').and.callThrough();

        deleteService.perform({name: 'ham'});
        $rootScope.$apply();

        expect($uibModal.open).toHaveBeenCalled();
        var spec = $uibModal.open.calls.mostRecent().args[0];
        expect(spec.controller).toBeDefined();
        expect(spec.templateUrl).toBeDefined();
        expect(spec.resolve).toBeDefined();
        expect(spec.resolve.selected).toBeDefined();
        expect(spec.resolve.selected()).toEqual([{name: 'ham'}]);

        // "close" the modal, make sure delete is called
        deferred.resolve();
        $rootScope.$apply();
        expect(actionResultService.getActionResult).toHaveBeenCalled();
      });
    });

    describe('editService', function test() {
      var swiftAPI, editService, modalWaitSpinnerService, toastService, $q;

      beforeEach(inject(function inject($injector, _$q_) {
        swiftAPI = $injector.get('horizon.app.core.openstack-service-api.swift');
        editService = $injector.get('horizon.dashboard.project.containers.objects-actions.edit');
        modalWaitSpinnerService = $injector.get(
          'horizon.framework.widgets.modal-wait-spinner.service'
        );
        toastService = $injector.get('horizon.framework.widgets.toast.service');
        $q = _$q_;
      }));

      it('should have an allowed and perform', function test() {
        expect(editService.allowed).toBeDefined();
        expect(editService.perform).toBeDefined();
      });

      it('should only allow files', function test() {
        expectAllowed(editService.allowed({is_object: true}));
      });

      it('should only now allow folders', function test() {
        expectNotAllowed(editService.allowed({is_object: false}));
      });

      it('should handle upload success correctly', function() {
        var modalDeferred = $q.defer();
        var apiDeferred = $q.defer();
        var result = { result: modalDeferred.promise };
        spyOn($uibModal, 'open').and.returnValue(result);
        spyOn(modalWaitSpinnerService, 'showModalSpinner');
        spyOn(modalWaitSpinnerService, 'hideModalSpinner');
        spyOn(swiftAPI, 'uploadObject').and.returnValue(apiDeferred.promise);
        spyOn(toastService, 'add').and.callThrough();
        spyOn(model,'updateContainer');
        spyOn(model,'selectContainer');

        editService.perform();
        model.container = {name: 'spam'};
        $rootScope.$apply();

        // Close the modal, make sure API call succeeds
        modalDeferred.resolve({name: 'ham', path: '/folder/ham'});
        apiDeferred.resolve();
        $rootScope.$apply();

        // Check the string of functions called by this code path succeed
        expect($uibModal.open).toHaveBeenCalled();
        expect(modalWaitSpinnerService.showModalSpinner).toHaveBeenCalled();
        expect(swiftAPI.uploadObject).toHaveBeenCalled();
        expect(toastService.add).toHaveBeenCalledWith('success', 'File /folder/ham uploaded.');
        expect(modalWaitSpinnerService.hideModalSpinner).toHaveBeenCalled();
        expect(model.updateContainer).toHaveBeenCalled();
        expect(model.selectContainer).toHaveBeenCalled();
      });

      it('should handle upload error correctly', function() {
        var modalDeferred = $q.defer();
        var apiDeferred = $q.defer();
        var result = { result: modalDeferred.promise };
        spyOn($uibModal, 'open').and.returnValue(result);
        spyOn(modalWaitSpinnerService, 'showModalSpinner');
        spyOn(modalWaitSpinnerService, 'hideModalSpinner');
        spyOn(swiftAPI, 'uploadObject').and.returnValue(apiDeferred.promise);
        spyOn(toastService, 'add').and.callThrough();
        spyOn(model,'updateContainer');
        spyOn(model,'selectContainer');

        editService.perform();
        model.container = {name: 'spam'};
        $rootScope.$apply();

        // Close the modal, make sure API call is rejected
        modalDeferred.resolve({name: 'ham', path: '/'});
        apiDeferred.reject();
        $rootScope.$apply();

        // Check the string of functions called by this code path succeed
        expect(modalWaitSpinnerService.showModalSpinner).toHaveBeenCalled();
        expect(swiftAPI.uploadObject).toHaveBeenCalled();
        expect(modalWaitSpinnerService.hideModalSpinner).toHaveBeenCalled();
        expect($uibModal.open).toHaveBeenCalled();

        // Check the success branch is not called
        expect(model.updateContainer).not.toHaveBeenCalled();
        expect(model.selectContainer).not.toHaveBeenCalled();
        expect(toastService.add).not.toHaveBeenCalledWith('success');
      });
    });

    describe('copyService', function test() {
      var swiftAPI, copyService, modalWaitSpinnerService, toastService, $q, objectDef;

      beforeEach(inject(function inject($injector, _$q_) {
        swiftAPI = $injector.get('horizon.app.core.openstack-service-api.swift');
        copyService = $injector.get('horizon.dashboard.project.containers.objects-actions.copy');
        modalWaitSpinnerService = $injector.get(
          'horizon.framework.widgets.modal-wait-spinner.service'
        );
        toastService = $injector.get('horizon.framework.widgets.toast.service');
        $q = _$q_;
      }));

      it('should have an allowed and perform', function test() {
        expect(copyService.allowed).toBeDefined();
        expect(copyService.perform).toBeDefined();
      });

      it('should only allow files which has size(bytes) over 0', function test() {
        objectDef = {
          is_object: true,
          bytes: 1
        };
        expectAllowed(copyService.allowed(objectDef));
      });

      it('should not allow folders', function test() {
        objectDef = {
          is_object: false,
          bytes: 1
        };
        expectNotAllowed(copyService.allowed(objectDef));
      });

      it('should not allow 0 byte file, because it means separated files', function test() {
        objectDef = {
          is_object: true,
          bytes: 0
        };
        expectNotAllowed(copyService.allowed(objectDef));
      });

      it('should handle copy success correctly', function() {
        var modalDeferred = $q.defer();
        var apiDeferred = $q.defer();
        var result = { result: modalDeferred.promise };
        spyOn($uibModal, 'open').and.returnValue(result);
        spyOn(modalWaitSpinnerService, 'showModalSpinner');
        spyOn(modalWaitSpinnerService, 'hideModalSpinner');
        spyOn(swiftAPI, 'copyObject').and.returnValue(apiDeferred.promise);
        spyOn(toastService, 'add').and.callThrough();
        spyOn(model,'updateContainer');
        spyOn(model,'selectContainer').and.returnValue(apiDeferred.promise);

        copyService.perform();
        model.container = {name: 'spam'};
        $rootScope.$apply();

        // Close the modal, make sure API call succeeds
        var sourceObjectPath = 'sourceObjectPath';
        modalDeferred.resolve({name: 'ham',
                               path: sourceObjectPath,
                               dest_container: 'dest_container',
                               dest_name: 'dest_name'});
        apiDeferred.resolve();
        $rootScope.$apply();

        // Check the string of functions called by this code path succeed
        expect($uibModal.open).toHaveBeenCalled();
        expect(modalWaitSpinnerService.showModalSpinner).toHaveBeenCalled();
        expect(swiftAPI.copyObject).toHaveBeenCalled();
        expect(toastService.add).
            toHaveBeenCalledWith('success', 'Object ' + sourceObjectPath +
            ' has copied.');
        expect(modalWaitSpinnerService.hideModalSpinner).toHaveBeenCalled();
        expect(model.updateContainer).toHaveBeenCalled();
        expect(model.selectContainer).toHaveBeenCalled();
      });

      it('should handle copy error correctly', function() {
        var modalDeferred = $q.defer();
        var apiDeferred = $q.defer();
        var result = { result: modalDeferred.promise };
        spyOn($uibModal, 'open').and.returnValue(result);
        spyOn(modalWaitSpinnerService, 'showModalSpinner');
        spyOn(modalWaitSpinnerService, 'hideModalSpinner');
        spyOn(swiftAPI, 'copyObject').and.returnValue(apiDeferred.promise);
        spyOn(toastService, 'add').and.callThrough();
        spyOn(model,'updateContainer');
        spyOn(model,'selectContainer').and.returnValue(apiDeferred.promise);

        copyService.perform();
        model.container = {name: 'spam'};
        $rootScope.$apply();

        // Close the modal, make sure API call succeeds
        var sourceObjectPath = 'sourceObjectPath';
        modalDeferred.resolve({name: 'ham',
                               path: sourceObjectPath,
                               dest_container: 'dest_container',
                               dest_name: 'dest_name'});
        apiDeferred.reject();
        $rootScope.$apply();

        // Check the string of functions called by this code path succeed
        expect(modalWaitSpinnerService.showModalSpinner).toHaveBeenCalled();
        expect(swiftAPI.copyObject).toHaveBeenCalled();
        expect(modalWaitSpinnerService.hideModalSpinner).toHaveBeenCalled();
        expect($uibModal.open).toHaveBeenCalled();

        // Check the success branch is not called
        expect(model.updateContainer).not.toHaveBeenCalled();
        expect(model.selectContainer).not.toHaveBeenCalled();
        expect(toastService.add).not.toHaveBeenCalledWith('success');
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

    function expectNotAllowed(promise) {
      var handler = exerciseAllowedPromise(promise);
      expect(handler.success).not.toHaveBeenCalled();
      expect(handler.error).toHaveBeenCalled();
    }
  });
})();
