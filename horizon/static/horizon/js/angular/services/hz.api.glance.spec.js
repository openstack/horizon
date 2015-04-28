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
    var service;
    var apiService = {};
    var toastService = {};

    beforeEach(module('hz.api'));

    beforeEach(module(function($provide) {
      window.apiTest.initServices($provide, apiService, toastService);
    }));

    beforeEach(inject(['hz.api.glance', function(glanceAPI) {
      service = glanceAPI;
    }]));

    it('defines the service', function() {
      expect(service).toBeDefined();
    });

    var tests = [
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
        window.apiTest.testCall.apply(this, callParams);
      });
    });

    it('supresses the error if instructed for getNamespaces', function() {
      spyOn(apiService, 'get').and.returnValue("promise");
      expect(service.getNamespaces("whatever", true)).toBe("promise");
    });

  });
})();
