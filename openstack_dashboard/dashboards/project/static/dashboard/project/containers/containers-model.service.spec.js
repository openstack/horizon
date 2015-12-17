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

    it('should load container contents', function test() {
      var deferred = $q.defer();
      spyOn(swiftAPI, 'getObjects').and.returnValue(deferred.promise);

      service.selectContainer('spam');

      expect(service.containerName).toEqual('spam');
      expect(swiftAPI.getObjects).toHaveBeenCalledWith('spam', {delimiter: '/'});

      deferred.resolve({data: {items: ['two', 'items']}});
      $rootScope.$apply();

      expect(service.objects).toEqual(['two', 'items']);
      expect(service.pseudo_folder_hierarchy).toEqual([]);
    });

    it('should load subfolder contents', function test() {
      var deferred = $q.defer();
      spyOn(swiftAPI, 'getObjects').and.returnValue(deferred.promise);

      service.selectContainer('spam', 'ham');

      expect(service.containerName).toEqual('spam');
      expect(service.folder).toEqual('ham');
      expect(swiftAPI.getObjects).toHaveBeenCalledWith('spam', {path: 'ham/', delimiter: '/'});

      deferred.resolve({data: {items: ['two', 'items']}});
      $rootScope.$apply();
      expect(service.objects).toEqual(['two', 'items']);
      expect(service.pseudo_folder_hierarchy).toEqual(['ham']);
    });
  });
})();
