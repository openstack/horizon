/*
 *    (c) Copyright 2015 Copyright 2015, Rackspace, US, Inc.
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

  describe('Swift API', function() {
    var testCall, service;
    var apiService = {};
    var toastService = {};

    beforeEach(
      module('horizon.mock.openstack-service-api',
        function($provide, initServices) {
          testCall = initServices($provide, apiService, toastService);
        })
    );

    beforeEach(module('horizon.app.core.openstack-service-api'));

    beforeEach(inject(['horizon.app.core.openstack-service-api.swift', function(swiftAPI) {
      service = swiftAPI;
    }]));

    it('defines the service', function() {
      expect(service).toBeDefined();
    });

    var tests = [
      {
        func: "getInfo",
        method: "get",
        path: "/api/swift/info/",
        error: "Unable to get the Swift service info."
      },
      {
        func: 'getContainers',
        method: 'get',
        path: '/api/swift/containers/',
        error: 'Unable to get the Swift container listing.',
        data: {}
      },
      {
        func: 'getContainer',
        method: 'get',
        path: '/api/swift/containers/spam/metadata/',
        error: 'Unable to get the container details.',
        testInput: [ 'spam' ]
      },
      {
        func: 'getPolicyDetails',
        method: 'get',
        path: '/api/swift/policies/',
        error: 'Unable to fetch the policy details.'
      },
      {
        func: 'createContainer',
        method: 'post',
        path: '/api/swift/containers/new-spam/metadata/',
        data: {is_public: false, storage_policy: 'nz--o1--mr-r3'},
        error: 'Unable to create the container.',
        testInput: [ 'new-spam', false, 'nz--o1--mr-r3' ]
      },
      {
        func: 'createContainer',
        method: 'post',
        path: '/api/swift/containers/new-spam/metadata/',
        data: {is_public: false, storage_policy: 'nz--o1--mr-r3'},
        error: 'Unable to create the container.',
        testInput: [ 'new-spam', false, 'nz--o1--mr-r3' ]
      },
      {
        func: 'createContainer',
        method: 'post',
        path: '/api/swift/containers/new-spam/metadata/',
        data: {is_public: true, storage_policy: 'nz--o1--mr-r3'},
        error: 'Unable to create the container.',
        testInput: [ 'new-spam', true, 'nz--o1--mr-r3' ]
      },
      {
        func: 'deleteContainer',
        method: 'delete',
        path: '/api/swift/containers/spam/metadata/',
        error: 'Unable to delete the container.',
        testInput: [ 'spam' ]
      },
      {
        func: 'setContainerAccess',
        method: 'put',
        data: {is_public: false},
        path: '/api/swift/containers/spam/metadata/',
        error: 'Unable to change the container access.',
        testInput: [ 'spam', false ]
      },
      {
        func: 'getObjects',
        method: 'get',
        data: {},
        path: '/api/swift/containers/spam/objects/',
        error: 'Unable to get the objects in container.',
        testInput: [ 'spam' ]
      },
      {
        func: 'getObjects',
        method: 'get',
        data: {params: {path: '/foo/bar'}},
        path: '/api/swift/containers/spam/objects/',
        error: 'Unable to get the objects in container.',
        testInput: [ 'spam', {path: '/foo/bar'} ]
      },
      {
        func: 'uploadObject',
        method: 'post',
        call_args: [
          '/api/swift/containers/spam/object/ham',
          {file: 'some junk'}
        ],
        error: 'Unable to upload the object.',
        testInput: [ 'spam', 'ham', 'some junk' ]
      },
      {
        func: 'deleteObject',
        method: 'delete',
        path: '/api/swift/containers/spam/object/ham',
        error: 'Unable to delete the object.',
        testInput: [ 'spam', 'ham' ]
      },
      {
        func: 'getObjectDetails',
        method: 'get',
        path: '/api/swift/containers/spam/metadata/ham',
        error: 'Unable to get details of the object.',
        testInput: [ 'spam', 'ham' ]
      },
      {
        func: 'createFolder',
        method: 'post',
        call_args: ['/api/swift/containers/spam/object/ham/', {}],
        error: 'Unable to create the folder.',
        testInput: [ 'spam', 'ham' ]
      },
      {
        func: 'copyObject',
        method: 'post',
        call_args: [
          '/api/swift/containers/spam/copy/ham',
          {dest_container: 'eggs', dest_name: 'bacon'}
        ],
        error: 'Unable to copy the object.',
        testInput: [ 'spam', 'ham', 'eggs', 'bacon' ]
      },
      {
        func: 'copyObject',
        method: 'post',
        call_args: [
          '/api/swift/containers/spam/copy/ham',
          {dest_container: 'eggs', dest_name: 'bacon'}
        ],
        error: 'Unable to copy the object.',
        testInput: [ 'spam', 'ham', 'eggs', 'bacon' ]
      }
    ];

    // Iterate through the defined tests and apply as Jasmine specs.
    angular.forEach(tests, function(params) {
      it('defines the ' + params.func + ' call properly', function test() {
        var callParams = [apiService, service, toastService, params];
        testCall.apply(this, callParams);
      });
    });

    it('returns a relevant error message when createFolder returns a 409 error', function test() {
      var promise = {error: angular.noop};
      spyOn(apiService, 'post').and.returnValue(promise);
      spyOn(promise, 'error');
      service.createFolder('spam', 'ham');
      spyOn(toastService, 'add');
      var innerFunc = promise.error.calls.argsFor(0)[0];
      // In the case of 409
      var message = 'A pseudo-folder with the name "ham" already exists.';
      innerFunc(message, 409);
      expect(toastService.add).toHaveBeenCalledWith('error', message);
    });

    it('returns a relevant error message when deleteContainer returns a 409 error',
      function test() {
        var promise = {error: angular.noop};
        spyOn(apiService, 'delete').and.returnValue(promise);
        spyOn(promise, 'error');
        service.deleteContainer('spam', 'ham');
        spyOn(toastService, 'add');
        var innerFunc = promise.error.calls.argsFor(0)[0];
        // In the case of 409
        var message = 'Unable to delete the container because it is not empty.';
        innerFunc(message, 409);
        expect(toastService.add).toHaveBeenCalledWith('error', message);
      }
    );

    it('returns a relevant error message when deleteObject returns a 409 error', function test() {
      var promise = {error: angular.noop};
      spyOn(apiService, 'delete').and.returnValue(promise);
      spyOn(promise, 'error');
      service.deleteObject('spam', 'ham');

      expect(apiService.delete).toHaveBeenCalledWith('/api/swift/containers/spam/object/ham');

      var innerFunc = promise.error.calls.argsFor(0)[0];
      expect(innerFunc).toBeDefined();
      spyOn(toastService, 'add');
      innerFunc({status: 409});
      expect(toastService.add).toHaveBeenCalledWith(
        'error',
        'Unable to delete the folder because it is not empty.'
      );
    });

    it('returns a relevant error message when copyObject returns a 409 error', function test() {
      var promise = {error: angular.noop};
      spyOn(apiService, 'post').and.returnValue(promise);
      spyOn(promise, 'error');
      service.copyObject('spam', 'ham', 'eggs', 'bacon');
      spyOn(toastService, 'add');
      var innerFunc = promise.error.calls.argsFor(0)[0];
      // In the case of 409
      var message = 'Some error message';
      innerFunc(message, 409);
      expect(toastService.add).toHaveBeenCalledWith('error', message);
    });

    it('getContainer suppresses errors when asked', function test() {
      var promise = {error: angular.noop};
      spyOn(apiService, 'get').and.returnValue(promise);
      spyOn(promise, 'error');
      spyOn(toastService, 'add');
      service.getContainer('spam', true);
      expect(promise.error).toHaveBeenCalledWith(angular.noop);
      expect(toastService.add).not.toHaveBeenCalled();
    });

    it('getObjectDetails suppresses errors when asked', function test() {
      var promise = {error: angular.noop};
      spyOn(apiService, 'get').and.returnValue(promise);
      spyOn(promise, 'error');
      spyOn(toastService, 'add');
      service.getObjectDetails('spam', 'ham', true);
      expect(promise.error).toHaveBeenCalledWith(angular.noop);
      expect(toastService.add).not.toHaveBeenCalled();
    });

    it('constructs container URLs', function test() {
      expect(service.getContainerURL('spam')).toEqual('/api/swift/containers/spam');
    });

    it('constructs container URLs with reserved characters', function test() {
      expect(service.getContainerURL('sp#m')).toEqual(
        '/api/swift/containers/sp%23m'
      );
    });

    it('constructs object URLs', function test() {
      expect(service.getObjectURL('spam', 'ham')).toEqual(
        '/api/swift/containers/spam/object/ham'
      );
    });

    it('constructs object URLs without munging any slashes', function test() {
      expect(service.getObjectURL('spam', 'ham/sam/i/am')).toEqual(
        '/api/swift/containers/spam/object/ham/sam/i/am'
      );
    });

    it('constructs object URLs for different functions', function test() {
      expect(service.getObjectURL('spam', 'ham', 'blah')).toEqual(
        '/api/swift/containers/spam/blah/ham'
      );
    });

    it('constructs object URLs with reserved characters', function test() {
      expect(service.getObjectURL('sp#m', 'ham/f#o')).toEqual(
        '/api/swift/containers/sp%23m/object/ham/f%23o'
      );
    });
  });

})();
