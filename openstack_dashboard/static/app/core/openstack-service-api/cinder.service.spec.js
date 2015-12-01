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

  describe('Cinder API', function() {
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

    beforeEach(inject(['horizon.app.core.openstack-service-api.cinder', function(cinderAPI) {
      service = cinderAPI;
    }]));

    it('defines the service', function() {
      expect(service).toBeDefined();
    });

    var tests = [
      {
        func: 'getVolumes',
        method: 'get',
        path: '/api/cinder/volumes/',
        data: { params: 'config' },
        error: 'Unable to retrieve the volumes.',
        testInput: [ 'config' ]
      },
      {
        func: 'getVolumes',
        method: 'get',
        path: '/api/cinder/volumes/',
        data: {},
        error: 'Unable to retrieve the volumes.'
      },
      {
        func: 'getVolume',
        method: 'get',
        path: '/api/cinder/volumes/1',
        error: 'Unable to retrieve the volume.',
        testInput: [1]
      },
      {
        func: 'getVolumeTypes',
        method: 'get',
        path: '/api/cinder/volumetypes/',
        error: 'Unable to retrieve the volume types.',
        testInput: []
      },
      {
        func: 'getVolumeType',
        method: 'get',
        path: '/api/cinder/volumetypes/1',
        error: 'Unable to retrieve the volume type.',
        testInput: [1]
      },
      {
        func: 'getDefaultVolumeType',
        method: 'get',
        path: '/api/cinder/volumetypes/default',
        error: 'Unable to retrieve the default volume type.',
        testInput: []
      },
      {
        'func': 'getExtensions',
        'method': 'get',
        'path': '/api/cinder/extensions/',
        'data': 'config',
        'error': 'Unable to retrieve the extensions.',
        'testInput': [
          'config'
        ]
      },
      {
        func: 'getVolumeSnapshots',
        method: 'get',
        path: '/api/cinder/volumesnapshots/',
        data: {},
        error: 'Unable to retrieve the volume snapshots.'
      },
      {
        func: 'getVolumeSnapshots',
        method: 'get',
        path: '/api/cinder/volumesnapshots/',
        data: { params: 'config' },
        error: 'Unable to retrieve the volume snapshots.',
        testInput: [ 'config' ]
      }
    ];

    // Iterate through the defined tests and apply as Jasmine specs.
    angular.forEach(tests, function(params) {
      it('defines the ' + params.func + ' call properly', function() {
        var callParams = [apiService, service, toastService, params];
        testCall.apply(this, callParams);
      });
    });

  });

})();
