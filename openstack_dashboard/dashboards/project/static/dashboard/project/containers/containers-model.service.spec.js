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

    var service, $q, $rootScope, swiftAPI, apiService;

    beforeEach(inject(function inject($injector, _$q_, _$rootScope_) {
      service = $injector.get('horizon.dashboard.project.containers.containers-model');
      $q = _$q_;
      $rootScope = _$rootScope_;
      swiftAPI = $injector.get('horizon.app.core.openstack-service-api.swift');
      apiService = $injector.get('horizon.framework.util.http.service');
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

      deferred.resolve({data: {items: [{name: 'two'}, {name: 'items'}]}});
      $rootScope.$apply();

      expect(service.objects).toEqual([
        { name: 'two', url: '/api/swift/containers/spam/object/two' },
        { name: 'items', url: '/api/swift/containers/spam/object/items' }
      ]);
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

      deferred.resolve({data: {items: [{name: 'two'}, {name: 'items'}]}});
      $rootScope.$apply();
      expect(service.objects).toEqual([
          { name: 'two', url: '/api/swift/containers/spam/object/ham/two' },
          { name: 'items', url: '/api/swift/containers/spam/object/ham/items' }
      ]);
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

    describe('recursive deletion', function describe() {
      // fake up a basic set of object listings to return from our fake getObjects
      // below
      var fakeSwift = {
        'file0': {path: 'file0', is_object: true},
        'folder/': [
          {path: 'folder/subfolder'},
          {path: 'folder/subfolder2'},
          {path: 'folder/subfolder3'},
          {path: 'folder/file1', is_object: true},
          {path: 'folder/file2', is_object: true}
        ],
        'folder/subfolder/': [
          {path: 'folder/subfolder/file3', is_object: true}
        ],
        'folder/subfolder2/': [       // exercises more than one folder
          {path: 'folder/subfolder2/file4', is_object: true}
        ],
        'folder/subfolder3/': []      // exercises empty folder
      };

      // and this is the tree generated by a recursive collect of the above
      var fakeTree = [
        'file0',
        {
          folder: 'folder',
          tree: [
            {
              folder: 'folder/subfolder',
              tree: [
                'folder/subfolder/file3'
              ]
            },
            {
              folder: 'folder/subfolder2',
              tree: [
                'folder/subfolder2/file4'
              ]
            },
            {
              folder: 'folder/subfolder3',
              tree: []
            },
            'folder/file1',
            'folder/file2'
          ]
        }
      ];

      beforeEach(function before() {
        spyOn(swiftAPI, 'getObjects').and.callFake(function fake(container, spec) {
          var deferred = $q.defer();
          var items = fakeSwift[spec.path];
          expect(items).toBeDefined();    // sanity check
          deferred.resolve({data: {items: items}});
          return deferred.promise;
        });
        service.container = {name: 'spam'};
      });

      it('should collect folder structure recursively', function test() {
        var state = {
          counted: {files: 0, folders: 0},
          cancel: false
        };
        var result = [];
        service.recursiveCollect(
          state,
          [{path: 'file0', is_object: true}, {path: 'folder', is_object: false}],
          result
        );

        // gotta resolve 'em all!
        $rootScope.$apply();

        expect(swiftAPI.getObjects).toHaveBeenCalled();
        expect(state.counted.files).toEqual(5);
        expect(state.counted.folders).toEqual(4);
        expect(result).toEqual(fakeTree);
      });

      it('should stop collection on cancel', function test() {
        var state = {
          counted: {files: 0, folders: 0},
          cancel: true
        };
        var result = [];

        service.recursiveCollect(
          state,
          [{path: 'file0', is_object: true}, {path: 'folder', is_object: false}],
          result
        );
        $rootScope.$apply();

        // cancel flag will prevent getObjects calls
        expect(swiftAPI.getObjects).not.toHaveBeenCalled();
        expect(state.counted.files).toEqual(1);
        expect(state.counted.folders).toEqual(0);
        expect(result).toEqual(['file0']);
      });

      it('should recursively delete files and then folders', function test() {
        var deferred = $q.defer();
        spyOn(service, '_recursiveDeleteFiles').and.returnValue(deferred.promise);
        spyOn(service, '_recursiveDeleteFolders');
        service.recursiveDelete('state', 'node');

        expect(service._recursiveDeleteFiles).toHaveBeenCalled();
        deferred.resolve();
        $rootScope.$apply();

        expect(service._recursiveDeleteFolders).toHaveBeenCalled();
      });

      it('should recursively delete files', function test() {
        var deletions = [];
        var state = {deleted: {files: 0}};
        spyOn(swiftAPI, 'deleteObject').and.callFake(function fake(container, node) {
          var deferred = $q.defer();
          deletions.push(node);
          deferred.resolve();
          return deferred.promise;
        });

        service._recursiveDeleteFiles(state, {tree: fakeTree});
        $rootScope.$apply();

        expect(deletions).toEqual([
          'file0',
          'folder/subfolder/file3',
          'folder/subfolder2/file4',
          'folder/file1',
          'folder/file2'
        ]);
        expect(state.deleted.files).toEqual(5);
      });

      // oh gods what have I wrought

      it('should recursively delete folders', function test() {
        var deletions = [];
        var state = {deleted: {folders: 0, failures: 0}};
        spyOn(apiService, 'delete').and.callFake(function fake(url) {
          var deferred = $q.defer();
          deletions.push(url);
          if (url === '/api/swift/containers/spam/object/folder/') {
            // pretend we're swift and we deleted the whole thing when we deleted the
            // leaf, like Swift sometimes does
            deferred.reject({status: 404});
          } else {
            deferred.resolve();
          }
          return deferred.promise;
        });

        service._recursiveDeleteFolders(state, {tree: fakeTree});
        $rootScope.$apply();
        expect(deletions).toEqual([
          '/api/swift/containers/spam/object/folder/subfolder3/',
          '/api/swift/containers/spam/object/folder/subfolder/',
          '/api/swift/containers/spam/object/folder/subfolder2/',
          '/api/swift/containers/spam/object/folder/'
        ]);
        expect(state.deleted.folders).toEqual(4);
        expect(state.deleted.failures).toEqual(0);
      });
    });
  });
})();
