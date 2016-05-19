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

    var rowActions, $modal, $rootScope, model;

    beforeEach(inject(function inject($injector, _$modal_, _$rootScope_) {
      rowActions = $injector.get('horizon.dashboard.project.containers.objects-row-actions');
      model = $injector.get('horizon.dashboard.project.containers.containers-model');
      $modal = _$modal_;
      $rootScope = _$rootScope_;
    }));

    it('should create an actions list', function test() {
      expect(rowActions.actions).toBeDefined();
      var actions = rowActions.actions();
      expect(actions.length).toEqual(3);
      angular.forEach(actions, function check(action) {
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
        spyOn($modal, 'open');
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

        expect($modal.open).toHaveBeenCalled();
        var spec = $modal.open.calls.mostRecent().args[0];
        expect(spec.backdrop).toBeDefined();
        expect(spec.controller).toBeDefined();
        expect(spec.templateUrl).toEqual('/base/path/object-details-modal.html');
        expect(swiftAPI.getObjectDetails).toHaveBeenCalledWith('spam', 'ham');
      });
    });

    describe('deleteService', function test() {
      var deleteService, $q;

      beforeEach(inject(function inject($injector, _$q_) {
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
        spyOn($modal, 'open').and.returnValue(result);
        spyOn(model, 'updateContainer');
        model.objects = [{name: 'ham'}, {name: 'too'}];

        deleteService.perform({name: 'ham'});
        $rootScope.$apply();

        expect($modal.open).toHaveBeenCalled();
        var spec = $modal.open.calls.mostRecent().args[0];
        expect(spec.controller).toBeDefined();
        expect(spec.templateUrl).toBeDefined();
        expect(spec.resolve).toBeDefined();
        expect(spec.resolve.selected).toBeDefined();
        expect(spec.resolve.selected()).toEqual([{checked: true, file: {name: 'ham'}}]);

        // "close" the modal, make sure delete is called
        deferred.resolve();
        $rootScope.$apply();
        expect(model.updateContainer).toHaveBeenCalled();
        expect(model.objects).toEqual([{name: 'too'}]);
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
