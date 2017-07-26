/*
 *    (c) Copyright 2015 Hewlett-Packard Development Company, L.P.
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

  describe('Glance API', function() {
    var testCall, service;
    var apiService = {};
    var toastService = {};

    beforeEach(function() {
      module('horizon.mock.openstack-service-api', function($provide, initServices) {
        testCall = initServices($provide, apiService, toastService);
      });

      module('horizon.app.core.openstack-service-api');

      inject(['horizon.app.core.openstack-service-api.glance', function(glanceAPI) {
        service = glanceAPI;
      }]);
    });

    it('defines the service', function() {
      expect(service).toBeDefined();
    });

    var tests = [
      {
        "func": "getVersion",
        "method": "get",
        "path": "/api/glance/version/",
        "error": "Unable to get the Glance service version."
      },
      {
        "func": "getImage",
        "method": "get",
        "path": "/api/glance/images/42/",
        "error": "Unable to retrieve the image.",
        "testInput": [
          42
        ]
      },
      {
        "func": "deleteImage",
        "method": "delete",
        "path": "/api/glance/images/42/",
        "error": "Unable to delete the image with id: 42",
        "testInput": [
          42
        ]
      },
      {
        "func": "updateImage",
        "method": "patch",
        "path": "/api/glance/images/1/",
        "data": {
          id: '1',
          name: '1'
        },
        "error": "Unable to update the image.",
        "testInput": [
          {name: '1', id: '1'}
        ]
      },
      {
        "func": "getImageProps",
        "method": "get",
        "path": "/api/glance/images/42/properties/",
        "error": "Unable to retrieve the image custom properties.",
        "testInput": [
          42
        ]
      },
      {
        "func": "editImageProps",
        "method": "patch",
        "path": "/api/glance/images/42/properties/",
        "data": {
          "updated": {a: '1', b: '2'},
          "removed": ['c', 'd']
        },
        "error": "Unable to edit the image custom properties.",
        "testInput": [
          42, {a: '1', b: '2'}, ['c', 'd']
        ]
      },
      {
        "func": "getImages",
        "method": "get",
        "path": "/api/glance/images/",
        "data": {
          "params": "config"
        },
        "error": "Unable to retrieve the images.",
        "testInput": [
          "config"
        ]
      },
      {
        "func": "getImages",
        "method": "get",
        "path": "/api/glance/images/",
        "data": {},
        "error": "Unable to retrieve the images."
      },
      {
        "func": "getNamespaces",
        "method": "get",
        "path": "/api/glance/metadefs/namespaces/",
        "data": {
          "params": {
            "orig": true
          },
          "cache": true
        },
        "error": "Unable to retrieve the namespaces.",
        "testInput": [
          {
            "orig": true
          }
        ]
      },
      {
        "func": "getNamespaces",
        "method": "get",
        "path": "/api/glance/metadefs/namespaces/",
        "data": {
          "cache": true
        },
        "error": "Unable to retrieve the namespaces."
      },
      {
        "func": "getResourceTypes",
        "method": "get",
        "path": "/api/glance/metadefs/resourcetypes/",
        "data": {
          "cache": true
        },
        "error": "Unable to retrieve the resource types."
      }
    ];

    // Iterate through the defined tests and apply as Jasmine specs.
    angular.forEach(tests, function(params) {
      it('defines the ' + params.func + ' call properly', function() {
        var callParams = [apiService, service, toastService, params];
        testCall.apply(this, callParams);
      });
    });

    it('supresses the error if instructed for getNamespaces', function() {
      spyOn(apiService, 'get').and.returnValue("promise");
      expect(service.getNamespaces("whatever", true)).toBe("promise");
    });

    it('supresses the error if instructed for deleteImage', function() {
      spyOn(apiService, 'delete').and.returnValue("promise");
      expect(service.deleteImage("whatever", true)).toBe("promise");
    });

    describe('createImage', function() {
      var $q, $rootScope, imageQueuedPromise, imageUploadPromise, onProgress;

      beforeEach(inject(function(_$q_, _$rootScope_) {
        $q = _$q_;
        $rootScope = _$rootScope_;
        imageQueuedPromise = $q.defer();
        imageUploadPromise = $q.defer();
        onProgress = jasmine.createSpy('onProgress');
        spyOn(apiService, 'put').and.returnValue(imageQueuedPromise.promise);
      }));

      it('shows error message when arguments are insufficient', function() {
        service.createImage.apply(null, [{name: 1}]);

        try {
          imageQueuedPromise.reject({'data': 'invalid'});
          $rootScope.$apply();
        } catch (error) {
          expect(error).toBeDefined();
          expect(error.data).toEqual('invalid');
        }

        expect(apiService.put).toHaveBeenCalledWith('/api/glance/images/', {name: 1});
      });

      it('shows a generic message when it gets a unexpected error', function() {
        service.createImage.apply(null, [{name: 1}]);

        try {
          imageQueuedPromise.reject();
          $rootScope.$apply();
        } catch (error) {
          expect(error).toBeDefined();
          expect(error).toEqual('Unable to create the image.');
        }

        expect(apiService.put).toHaveBeenCalledWith('/api/glance/images/', {name: 1});
      });

      describe('external upload of a local file', function() {
        var fakeFile = {name: 'test file'};
        var imageData = {
          name: 'test', source_type: 'file-direct', diskFormat: 'iso', data: fakeFile
        };
        var queuedImage = {
          'name': imageData.name,
          'upload_url': 'http://sample.com',
          'token_id': 'my token'
        };

        beforeEach(function() {
          apiService.put.and.returnValues(
            imageQueuedPromise.promise,
            imageUploadPromise.promise);
          service.createImage(imageData, onProgress);
        });

        it('does not send the file itself during the first call', function() {
          var passedImageData = angular.extend({}, imageData, {data: fakeFile.name});
          expect(apiService.put.calls.argsFor(0)).toEqual(['/api/glance/images/', passedImageData]);
        });

        it('second call is not made until the image is created', function() {
          expect(apiService.put.calls.count()).toBe(1);

          imageQueuedPromise.resolve({data: queuedImage});
          $rootScope.$apply();

          expect(apiService.put.calls.count()).toBe(2);
        });

        it('second call is not started if the initial image creation fails', function() {
          try {
            imageQueuedPromise.reject({'data': 'invalid'});
            $rootScope.$apply();
          } catch (error) {
            expect(error).toBeDefined();
            expect(error.data).toEqual('invalid');
          }

          expect(apiService.put.calls.count()).toBe(1);
        });

        it('uses data from the initially created image', function() {
          imageQueuedPromise.resolve({data: queuedImage});
          $rootScope.$apply();

          expect(apiService.put).toHaveBeenCalledWith(
            queuedImage.upload_url,
            fakeFile,
            {
              headers: {
                'X-Auth-Token': queuedImage.token_id,
                'Content-Type': 'application/octet-stream'
              },
              external: true
            }
          );
        });

        it('second call is not started if image creation returns no upload_url', function() {
          var missingUrl = {
            'name': imageData.name,
            'token_id': 'my token'
          };
          imageQueuedPromise.resolve({data: missingUrl});
          $rootScope.$apply();

          expect(apiService.put.calls.count()).toBe(1);
        });

        it('sends back upload progress', function() {
          imageQueuedPromise.resolve({data: queuedImage});
          $rootScope.$apply();
          imageUploadPromise.notify({
            loaded: 1,
            total: 2
          });
          imageUploadPromise.notify({
            loaded: 2,
            total: 2
          });
          imageUploadPromise.resolve();
          $rootScope.$apply();

          expect(onProgress.calls.allArgs()).toEqual([[50], [100]]);
        });

      });

      describe('proxied (AKA legacy) upload of a local file', function() {
        var fakeFile = {name: 'test file'};
        var imageData = {
          name: 'test', source_type: 'file-legacy', diskFormat: 'iso', data: fakeFile
        };

        beforeEach(function() {
          spyOn(apiService, 'post').and.returnValue(imageUploadPromise.promise);
          service.createImage(imageData, onProgress);
        });

        it('emits one POST and not PUTs', function() {
          expect(apiService.post.calls.count()).toBe(1);
          expect(apiService.put).not.toHaveBeenCalled();
        });

        it('sends the file itself during the POST call', function() {
          expect(apiService.post).toHaveBeenCalledWith('/api/glance/images/', imageData);
        });

        it('sends back upload progress', function() {
          imageUploadPromise.notify({
            loaded: 1,
            total: 2
          });
          imageUploadPromise.notify({
            loaded: 2,
            total: 2
          });
          $rootScope.$apply();

          expect(onProgress.calls.allArgs()).toEqual([[50], [100]]);
        });
      });

    });

  });

})();
