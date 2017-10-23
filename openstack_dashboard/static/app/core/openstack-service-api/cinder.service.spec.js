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
        func: 'getVolumeMetadata',
        method: 'get',
        path: '/api/cinder/volumes/1/metadata',
        error: 'Unable to retrieve the volume metadata.',
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
        func: 'getVolumeTypeMetadata',
        method: 'get',
        path: '/api/cinder/volumetypes/1/metadata',
        error: 'Unable to retrieve the volume type metadata.',
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
      { func: 'getServices',
        method: 'get',
        path: '/api/cinder/services/',
        error: 'Unable to retrieve the cinder services.' },

      { func: 'getVolumeSnapshots',
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
      },
      {
        func: 'getVolumeSnapshotMetadata',
        method: 'get',
        path: '/api/cinder/volumesnapshots/1/metadata',
        error: 'Unable to retrieve the snapshot metadata.',
        testInput: [1]
      },
      {
        func: 'createVolume',
        method: 'post',
        path: '/api/cinder/volumes/',
        data: { params: 'config' },
        error: 'Unable to create the volume.',
        testInput: [
          {
            params: 'config'
          }
        ]
      },
      {
        func: 'getQoSSpecs',
        method: 'get',
        path: '/api/cinder/qosspecs/',
        data: {},
        error: 'Unable to retrieve the QoS Specs.'
      },
      {
        func: 'getQoSSpecs',
        method: 'get',
        path: '/api/cinder/qosspecs/',
        data: { params: 'config' },
        error: 'Unable to retrieve the QoS Specs.',
        testInput: [ 'config' ]
      },
      {
        func: 'getDefaultQuotaSets',
        method: 'get',
        path: '/api/cinder/quota-sets/defaults/',
        error: 'Unable to retrieve the default quotas.'
      },
      {
        func: 'setDefaultQuotaSets',
        "data": {
          "id": 42
        },
        "testInput": [
          {
            "id": 42
          }
        ],
        method: 'patch',
        path: '/api/cinder/quota-sets/defaults/',
        error: 'Unable to set the default quotas.'
      },
      { func: 'updateProjectQuota',
        method: 'patch',
        path: '/api/cinder/quota-sets/42',
        data: {'volumes': 42},
        error: 'Unable to update project quota data.',
        testInput: [{'volumes': 42}, 42]
      },
      { func: 'editVolumeMetadata',
        method: 'patch',
        path: '/api/cinder/volumes/42/metadata',
        data: {
          "updated": {a: '1', b: '2'},
          "removed": ['c', 'd']
        },
        error: "Unable to edit volume metadata.",
        testInput: [
          42, {a: '1', b: '2'}, ['c', 'd']
        ]
      },
      { func: 'editVolumeSnapshotMetadata',
        method: 'patch',
        path: '/api/cinder/volumesnapshots/42/metadata',
        data: {
          "updated": {a: '1', b: '2'},
          "removed": ['c', 'd']
        },
        error: "Unable to edit snapshot metadata.",
        testInput: [
          42, {a: '1', b: '2'}, ['c', 'd']
        ]
      },
      { func: 'editVolumeTypeMetadata',
        method: 'patch',
        path: '/api/cinder/volumetypes/42/metadata',
        data: {
          "updated": {a: '1', b: '2'},
          "removed": ['c', 'd']
        },
        error: "Unable to edit volume type metadata.",
        testInput: [
          42, {a: '1', b: '2'}, ['c', 'd']
        ]
      },
      {
        func: 'getAvailabilityZones',
        method: 'get',
        path: '/api/cinder/availzones/',
        error: 'Unable to retrieve the volume availability zones.',
        testInput: []
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
