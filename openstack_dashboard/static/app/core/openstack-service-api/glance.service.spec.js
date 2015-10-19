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
        "path": "/api/glance/images/42",
        "error": "Unable to retrieve the image.",
        "testInput": [
          42
        ]
      },
      {
        "func": "deleteImage",
        "method": "delete",
        "path": "/api/glance/images/42",
        "error": "Unable to delete the image with id: 42",
        "testInput": [
          42
        ]
      },
      {
        "func": "createImage",
        "method": "post",
        "path": "/api/glance/images/",
        "data": {
          name: '1'
        },
        "error": "Unable to create the image.",
        "testInput": [
          {name: '1'}
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

  });

})();
