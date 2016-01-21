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
    beforeEach(module('horizon.framework'));
    beforeEach(module('horizon.dashboard.project.containers'));

    var service, $q, $rootScope, swiftAPI;

    beforeEach(inject(function inject($injector, _$q_, _$rootScope_) {
      service = $injector.get('horizon.dashboard.project.containers.containers-model');
      $q = _$q_;
      $rootScope = _$rootScope_;
      swiftAPI = $injector.get('horizon.app.core.openstack-service-api.swift');
    }));

    it('should initialise the model', function test() {
      expect(service.containers).toBeDefined();
      expect(service.DELIMETER).toBeDefined();
    });

    it('should retrieve the swift info and user containers on initalize()', function test() {
      var infoDeferred = $q.defer();
      spyOn(swiftAPI, 'getInfo').and.returnValue(infoDeferred.promise);
      var containersDeferred = $q.defer();
      spyOn(swiftAPI, 'getContainers').and.returnValue(containersDeferred.promise);

      service.initialize();
      expect(swiftAPI.getInfo).toHaveBeenCalled();
      expect(swiftAPI.getContainers).toHaveBeenCalled();

      infoDeferred.resolve({info: 'spam'});
      containersDeferred.resolve({data: {items: ['two', 'items']}});
      $rootScope.$apply();

      expect(service.swift_info).toEqual('spam');
      expect(service.containers).toEqual(['two', 'items']);
    });

    it('should select containers and load contents', function test() {
      var deferred = $q.defer();
      spyOn(swiftAPI, 'getObjects').and.returnValue(deferred.promise);
      service.containers = [{name: 'spam'}, {name: 'not spam'}];

      service.selectContainer('spam');

      expect(service.container.name).toEqual('spam');
      expect(swiftAPI.getObjects).toHaveBeenCalledWith('spam', {delimiter: '/'});

      deferred.resolve({data: {items: ['two', 'items']}});
      $rootScope.$apply();

      expect(service.objects).toEqual(['two', 'items']);
      expect(service.pseudo_folder_hierarchy).toEqual([]);
    });

    it('should load subfolder contents', function test() {
      var deferred = $q.defer();
      spyOn(swiftAPI, 'getObjects').and.returnValue(deferred.promise);
      service.containers = [{name: 'spam'}];

      service.selectContainer('spam', 'ham');

      expect(service.container.name).toEqual('spam');
      expect(service.folder).toEqual('ham');
      expect(swiftAPI.getObjects).toHaveBeenCalledWith('spam', {path: 'ham/', delimiter: '/'});

      deferred.resolve({data: {items: ['two', 'items']}});
      $rootScope.$apply();
      expect(service.objects).toEqual(['two', 'items']);
      expect(service.pseudo_folder_hierarchy).toEqual(['ham']);
    });

    it('should fetch container detail', function test() {
      var deferred = $q.defer();
      spyOn(swiftAPI, 'getContainer').and.returnValue(deferred.promise);

      var container = {name: 'spam'};
      service.fetchContainerDetail(container);

      expect(swiftAPI.getContainer).toHaveBeenCalledWith('spam');

      deferred.resolve({data: { info: 'yes!', timestamp: '2016-02-03T16:38:42.0Z' }});
      $rootScope.$apply();

      expect(container.info).toEqual('yes!');
      expect(container.timestamp).toBeDefined();
      expect(container.timestamp).toEqual(new Date(Date.UTC(2016, 1, 3, 16, 38, 42, 0)));
    });

    it('should handle bad timestamp data', function test() {
      var deferred = $q.defer();
      spyOn(swiftAPI, 'getContainer').and.returnValue(deferred.promise);

      var container = {name: 'spam'};
      service.fetchContainerDetail(container);

      expect(swiftAPI.getContainer).toHaveBeenCalledWith('spam');

      deferred.resolve({data: { info: 'yes!', timestamp: 'b0rken' }});
      $rootScope.$apply();

      expect(container.info).toEqual('yes!');
      expect(container.timestamp).toBeDefined();
      expect(container.timestamp).toEqual('b0rken');
    });

    it('should not re-fetch container detail', function test() {
      spyOn(swiftAPI, 'getContainer');
      var container = {name: 'spam', is_fetched: true};
      service.fetchContainerDetail(container);

      expect(swiftAPI.getContainer).not.toHaveBeenCalled();
      expect(container.info).toBeUndefined();
    });

    it('should not re-fetch container detail unless forced', function test() {
      var deferred = $q.defer();
      spyOn(swiftAPI, 'getContainer').and.returnValue(deferred.promise);

      var container = {name: 'spam', is_fetched: true};
      service.fetchContainerDetail(container, true);

      expect(swiftAPI.getContainer).toHaveBeenCalledWith('spam');

      deferred.resolve({data: { info: 'yes!', timestamp: 'b0rken' }});
      $rootScope.$apply();

      expect(container.info).toEqual('yes!');
    });

    it('should update containers', function test() {
      spyOn(service, 'fetchContainerDetail');
      service.container = {name: 'one'};
      service.updateContainer();
      expect(service.fetchContainerDetail).toHaveBeenCalledWith(service.container, true);
    });

    it('should delete objects', function test() {
      service.container = {name: 'spam'};
      service.objects = [{name: 'one'}, {name: 'two'}];
      var deferred = $q.defer();
      spyOn(swiftAPI, 'deleteObject').and.returnValue(deferred.promise);

      service.deleteObject(service.objects[0]);

      expect(swiftAPI.deleteObject).toHaveBeenCalledWith('spam', 'one');

      deferred.resolve();
      $rootScope.$apply();

      expect(service.objects).toEqual([{name: 'two'}]);
    });

    it('should delete folders', function test() {
      service.container = {name: 'spam'};
      service.objects = [{name: 'one', is_subdir: true}, {name: 'two'}];
      var deferred = $q.defer();
      spyOn(swiftAPI, 'deleteObject').and.returnValue(deferred.promise);

      service.deleteObject(service.objects[0]);

      // note trailing slash to indicate we're deleting the "folder"
      expect(swiftAPI.deleteObject).toHaveBeenCalledWith('spam', 'one/');

      deferred.resolve();
      $rootScope.$apply();

      expect(service.objects).toEqual([{name: 'two'}]);
    });
  });
})();
