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

  describe('Launch Instance Model', function() {

    describe('launchInstanceModel Factory', function() {
      var model, scope, settings, $q, glance, IMAGE, VOLUME, VOLUME_SNAPSHOT, INSTANCE_SNAPSHOT;
      var cinderEnabled = false;
      var neutronEnabled = false;
      var novaExtensionsEnabled = false;
      var ifAllowedResolve = true;

      var novaApi = {
        createServer: function(finalSpec) {
          return {
            then: function () {
              return finalSpec;
            }
          };
        },
        getAvailabilityZones: function() {
          var zones = [
            { zoneName: 'zone-1', zoneState: { available: true } },
            { zoneName: 'zone-2', zoneState: { available: true } },
            { zoneName: 'invalid-zone-1' },
            { zoneName: 'invalid-zone-2' }
          ];

          var deferred = $q.defer();
          deferred.resolve({ data: { items: zones } });

          return deferred.promise;
        },
        getFlavors: function() {
          var flavors = [ 'flavor-1', 'flavor-2' ];

          var deferred = $q.defer();
          deferred.resolve({ data: { items: flavors } });

          return deferred.promise;
        },
        getKeypairs: function() {
          var keypairs = [ { keypair: { name: 'key-1' } },
                           { keypair: { name: 'key-2' } } ];

          var deferred = $q.defer();
          deferred.resolve({ data: { items: keypairs } });

          return deferred.promise;
        },
        getLimits: function() {
          var limits = { maxTotalInstances: 10, totalInstancesUsed: 0 };

          var deferred = $q.defer();
          deferred.resolve({ data: limits });

          return deferred.promise;
        },
        getServerGroups: function() {
          var serverGroups = [ {'id': 'group-1'}, {'id': 'group-2'} ];

          var deferred = $q.defer();
          deferred.resolve({ data: { items: serverGroups } });

          return deferred.promise;
        }
      };

      var securityGroupApi = {
        query: function() {
          var secGroups = [
            { name: 'security-group-1' },
            { name: 'security-group-2' }
          ];

          var deferred = $q.defer();
          deferred.resolve({ data: { items: secGroups } });
          return deferred.promise;
        }
      };

      var neutronApi = {
        getNetworks: function() {
          var networks = [
            { id: 'net-1', subnets: [ { id: 'subnet1' } ] },
            { id: 'net-2', subnets: [ { id: 'subnet2' } ] },
            { id: 'net-3', subnets: []}
          ];

          var deferred = $q.defer();
          deferred.resolve({ data: { items: networks } });

          return deferred.promise;
        },
        getPorts: function(network) {
          var ports = {
            'net-1': [
              { name: 'port-1', device_owner: '', fixed_ips: [], admin_state: 'UP' },
              { name: 'port-2', device_owner: '', fixed_ips: [], admin_state: 'DOWN' }
            ],
            'net-2': [
              { name: 'port-3', device_owner: 'owner', fixed_ips: [], admin_state: 'DOWN' },
              { name: 'port-4', device_owner: '', fixed_ips: [], admin_state: 'DOWN' }
            ],
            'net-3': []
          };

          var deferred = $q.defer();
          deferred.resolve({ data: { items: ports[network.network_id] } });

          return deferred.promise;
        }
      };

      beforeEach(module('horizon.dashboard.project.workflow.launch-instance'));

      beforeEach(module(function($provide) {
        $provide.value('horizon.app.core.openstack-service-api.glance', {
          getImages: function () {
            var images = [
              {container_format: 'aki', properties: {}},
              {container_format: 'ari', properties: {}},
              {container_format: 'ami', properties: {}},
              {container_format: 'raw', properties: {}},
              {container_format: 'ami', properties: {image_type: 'image'}},
              {container_format: 'raw', properties: {image_type: 'image'}},
              {container_format: 'ami', properties: {
                block_device_mapping: '[{"source_type": "snapshot"}]'}},
              {container_format: 'raw', properties: {
                block_device_mapping: '[{"source_type": "snapshot"}]'}}
            ];

            var deferred = $q.defer();
            deferred.resolve({data: {items: images}});

            return deferred.promise;
          },
          getNamespaces: function () {
            var namespaces = ['ns-1', 'ns-2'];

            var deferred = $q.defer();
            deferred.resolve({data: {items: namespaces}});

            return deferred.promise;
          }
        });

        beforeEach(function () {
          settings = {
            LAUNCH_INSTANCE_DEFAULTS: {
              create_volume: true,
              hide_create_volume: false,
              config_drive: false,
              disable_image: false,
              disable_instance_snapshot: false,
              disable_volume: false,
              disable_volume_snapshot: false
            }
          };
          IMAGE = {type: 'image', label: 'Image'};
          VOLUME = {type: 'volume', label: 'Volume'};
          VOLUME_SNAPSHOT = {type: 'volume_snapshot', label: 'Volume Snapshot'};
          INSTANCE_SNAPSHOT = {type: 'snapshot', label: 'Instance Snapshot'};
        });
        $provide.value('horizon.app.core.openstack-service-api.nova', novaApi);

        $provide.value('horizon.app.core.openstack-service-api.security-group', securityGroupApi);

        $provide.value('horizon.app.core.openstack-service-api.neutron', neutronApi);

        $provide.value('horizon.app.core.openstack-service-api.cinder', {
          getVolumes: function() {
            var volumes = [ { id: 'vol-1' }, { id: 'vol-2' } ];

            var deferred = $q.defer();
            deferred.resolve({ data: { items: volumes } });

            return deferred.promise;
          },
          getVolumeSnapshots: function() {
            var snapshots = [ { id: 'snap-1', volume_id: 'vol-1' },
                              { id: 'snap-2', volume_id: 'vol-2' },
                              { id: 'snap-3', volume_id: 'vol-3' } ];

            var deferred = $q.defer();
            deferred.resolve({ data: { items: snapshots } });

            return deferred.promise;
          },
          getAbsoluteLimits: function() {
            var limits = { maxTotalVolumes: 100,
                           totalVolumesUsed: 2,
                           maxTotalVolumeGigabytes: 1000,
                           totalGigabytesUsed: 10 };
            var deferred = $q.defer();
            deferred.resolve({ data: limits });
            return deferred.promise;
          }
        });

        $provide.value('horizon.app.core.openstack-service-api.serviceCatalog', {
          ifTypeEnabled: function(theType) {
            var deferred = $q.defer();

            if (theType === 'network' && neutronEnabled) {
              deferred.resolve();
            } else if (theType === 'volumev2' && cinderEnabled) {
              deferred.resolve();
            } else if (theType === 'volumev3' && cinderEnabled) {
              deferred.resolve();
            } else {
              deferred.reject();
            }

            return deferred.promise;
          }
        });

        $provide.value('horizon.app.core.openstack-service-api.policy', {
          ifAllowed: function() {
            var deferred = $q.defer();

            if (ifAllowedResolve) {
              deferred.resolve();
            } else {
              deferred.reject();
            }
            return deferred.promise;
          },
          check: function() {
            var deferred = $q.defer();

            deferred.resolve();

            return deferred.promise;
          }
        });

        $provide.value('horizon.app.core.openstack-service-api.novaExtensions', {
          ifNameEnabled: function() {
            var deferred = $q.defer();

            if (novaExtensionsEnabled) {
              deferred.resolve();
            } else {
              deferred.reject();
            }

            return deferred.promise;
          }
        });

        $provide.value('horizon.app.core.openstack-service-api.settings', {
          getSetting: function(setting) {
            var deferred = $q.defer();

            deferred.resolve(settings[setting]);

            return deferred.promise;
          },
          ifEnabled: function(setting) {
            var deferred = $q.defer();

            var keys = setting.split('.');
            var index = 0;
            var value = settings;
            while (angular.isObject(value) && index < keys.length) {
              value = value[keys[index]];
              index++;
            }

            // NOTE: This does not work for the general case of ifEnabled, only for what
            // we need it for at the moment (only explicit false rejects the promise).
            if (value === false) {
              deferred.reject();
            } else {
              deferred.resolve();
            }

            return deferred.promise;
          }
        });

        $provide.value('horizon.framework.widgets.toast.service', {
          add: function() {}
        });
      }));

      beforeEach(inject(function($injector) {
        model = $injector.get('launchInstanceModel');
        $q = $injector.get('$q');
        scope = $injector.get('$rootScope').$new();
        glance = $injector.get('horizon.app.core.openstack-service-api.glance');
        spyOn(glance, 'getNamespaces').and.callThrough();
        spyOn(novaApi, 'getServerGroups').and.callThrough();
      }));

      describe('Initial object (pre-initialize)', function() {

        it('is defined', function() {
          expect(model).toBeDefined();
        });

        it('has initialization status parameters', function() {
          expect(model.initializing).toBeDefined();
          expect(model.initialized).toBeDefined();
        });

        it('has an empty newInstanceSpec', function() {
          expect(model.newInstanceSpec).toEqual({});
        });

        it('has empty arrays for all data', function() {
          var datasets = ['availabilityZones', 'flavors', 'allowedBootSources',
            'images', 'imageSnapshots', 'keypairs', 'networks',
            'securityGroups', 'serverGroups', 'volumes',
            'volumeSnapshots'];

          datasets.forEach(function(name) {
            expect(model[name]).toEqual([]);
          });
        });

        it('initialized metadatadefs to null values', function() {
          expect(model.metadataDefs.flavor).toBeNull();
          expect(model.metadataDefs.image).toBeNull();
          expect(model.metadataDefs.volume).toBeNull();
          expect(model.metadataDefs.instance).toBeNull();
          expect(model.metadataDefs.hints).toBeNull();
          expect(Object.keys(model.metadataDefs).length).toBe(5);
        });

        it('defaults "allow create volume from image" to false', function() {
          expect(model.allowCreateVolumeFromImage).toBe(false);
        });

        it('defaults "volume bootable" to false', function() {
          expect(model.volumeBootable).toBe(false);
        });

        it('defaults "metadataTree" to null', function() {
          expect(model.metadataTree).toBe(null);
        });

        it('defaults "hintsTree" to null', function() {
          expect(model.hintsTree).toBe(null);
        });

        it('initializes "nova limits" to empty object', function() {
          expect(model.novaLimits).toEqual({});
        });

        it('has an "initialize" function', function() {
          expect(model.initialize).toBeDefined();
        });

        it('has a "createInstance" function', function() {
          expect(model.createInstance).toBeDefined();
        });

      });

      describe('Post Initialize Model', function() {

        it('should init model with no networks/volumes if neutron & cinder disabled', function() {
          model.initialize(true);
          scope.$apply();

          expect(model.initializing).toBe(false);
          expect(model.initialized).toBe(true);
          expect(model.newInstanceSpec).toBeDefined();

          var expectedImages = [
            {container_format: 'ami', properties: {}},
            {container_format: 'raw', properties: {}},
            {container_format: 'ami', properties: {image_type: 'image'}},
            {container_format: 'raw', properties: {image_type: 'image'}}
          ];
          expect(model.images).toEqual(expectedImages);

          var expectedSnapshots = [
            {
              container_format: 'ami',
              properties: {block_device_mapping: '[{"source_type": "snapshot"}]'}
            },
            {
              container_format: 'raw',
              properties: {block_device_mapping: '[{"source_type": "snapshot"}]'}
            }
          ];
          expect(model.imageSnapshots).toEqual(expectedSnapshots);

          var expectedZones = [
            {'label': 'Any Availability Zone', 'value': ''},
            {'label': 'zone-1', 'value': 'zone-1'},
            {'label': 'zone-2', 'value': 'zone-2'}
          ];
          expect(model.availabilityZones).toEqual(expectedZones);

          var expectedFlavors = ['flavor-1', 'flavor-2'];
          expect(model.flavors).toEqual(expectedFlavors);

          var expectedKeypairs = [
            {'name': 'key-1', id: 'li_keypair:key-1'},
            {'name': 'key-2', id: 'li_keypair:key-2'}
          ];
          expect(model.keypairs).toEqual(expectedKeypairs);

          var expectedSecurityGroups = [
            {name: 'security-group-1'},
            {name: 'security-group-2'}
          ];
          expect(model.securityGroups).toEqual(expectedSecurityGroups);

          var expectedLimits = {maxTotalInstances: 10, totalInstancesUsed: 0};
          expect(model.novaLimits).toEqual(expectedLimits);
        });

        it('should have networks & no volumes if neutron enabled & cinder disabled', function() {
          neutronEnabled = true;
          cinderEnabled = false;
          model.initialize(true);
          scope.$apply();

          expect(model.neutronEnabled).toBe(true);
          expect(model.networks.length).toBe(2);
          expect(model.volumes.length).toBe(0);
        });

        it('should have volumes & no networks if neutron disabled & cinder enabled', function() {
          neutronEnabled = false;
          cinderEnabled = true;
          model.initialize(true);
          scope.$apply();

          expect(model.networks.length).toBe(0);
          expect(model.volumes.length).toBe(2);
          expect(model.volumeSnapshots.length).toBe(2);
        });

        it('should have networks and volumes if neutron and cinder enabled', function() {
          neutronEnabled = true;
          cinderEnabled = true;
          model.initialize(true);
          scope.$apply();

          expect(model.networks.length).toBe(2);
          expect(model.volumes.length).toBe(2);
          expect(model.volumeSnapshots.length).toBe(2);
        });

        it('should disable create volume from image if nova extensions disabled', function() {
          cinderEnabled = true;
          novaExtensionsEnabled = false;
          model.initialize(true);
          scope.$apply();

          expect(model.allowCreateVolumeFromImage).toBe(false);
        });

        it('should default config_drive to false', function() {
          model.initialize(true);
          scope.$apply();

          expect(model.newInstanceSpec.config_drive).toBe(false);
        });

        it('should default config_drive to false if setting not provided', function() {
          delete settings.LAUNCH_INSTANCE_DEFAULTS.config_drive;
          model.initialize(true);
          scope.$apply();

          expect(model.newInstanceSpec.config_drive).toBe(false);
        });

        it('should default config_drive to true based on setting', function() {
          settings.LAUNCH_INSTANCE_DEFAULTS.config_drive = true;
          model.initialize(true);
          scope.$apply();

          expect(model.newInstanceSpec.config_drive).toBe(true);
        });

        it('should default create_volume to true if setting not provided', function() {
          delete settings.LAUNCH_INSTANCE_DEFAULTS.create_volume;
          model.initialize(true);
          scope.$apply();

          expect(model.newInstanceSpec.create_volume_default).toBe(true);
        });

        it('should default create_volume to false based on setting', function() {
          settings.LAUNCH_INSTANCE_DEFAULTS.create_volume = false;
          model.initialize(true);
          scope.$apply();

          expect(model.newInstanceSpec.create_volume_default).toBe(false);
        });

        it('should default hide_create_volume to false if setting not provided', function() {
          delete settings.LAUNCH_INSTANCE_DEFAULTS.hide_create_volume;
          model.initialize(true);
          scope.$apply();

          expect(model.newInstanceSpec.hide_create_volume).toBe(false);
        });

        it('should default hide_create_volume to true based on setting', function() {
          settings.LAUNCH_INSTANCE_DEFAULTS.hide_create_volume = true;
          model.initialize(true);
          scope.$apply();

          expect(model.newInstanceSpec.hide_create_volume).toBe(true);
        });

        it('should not set availability zone if the zone list is empty', function () {
          spyOn(novaApi, 'getAvailabilityZones').and.callFake(function () {
            var deferred = $q.defer();
            deferred.resolve({ data: { items: [] } });
            return deferred.promise;
          });
          model.initialize(true);
          scope.$apply();
          expect(model.availabilityZones.length).toBe(0);
          expect(model.newInstanceSpec.availability_zone).toBe(null);
        });

        it('sets the ports properly based on device_owner', function () {
          model.initialize(true);
          scope.$apply();
          expect(model.ports.length).toBe(1);
        });

        it('should make 5 requests for namespaces', function() {
          model.initialize(true);
          scope.$apply();
          expect(glance.getNamespaces.calls.count()).toBe(5);
        });

        it('should not request scheduler hints if scheduler hints disabled', function() {
          settings.LAUNCH_INSTANCE_DEFAULTS.enable_scheduler_hints = false;
          model.initialize(true);
          scope.$apply();
          expect(glance.getNamespaces.calls.count()).toBe(4);
        });

        it('should set a keypair by default if only one keypair is available', function () {
          var keypair = { keypair: { name: 'key-1' } };
          spyOn(novaApi, 'getKeypairs').and.callFake(function () {
            var deferred = $q.defer();
            deferred.resolve({ data: { items: [ keypair ] } });
            return deferred.promise;
          });
          model.initialize(true);
          scope.$apply();
          expect(model.newInstanceSpec.key_pair.length).toBe(1);
          expect(model.newInstanceSpec.key_pair).toEqual([ keypair.keypair ]);
        });

        it('should set a security group by default if one named "default" is available',
          function () {
            var secGroups = [ { name: 'default' } ];
            spyOn(securityGroupApi, 'query').and.callFake(function () {
              var deferred = $q.defer();
              deferred.resolve({ data: { items: secGroups } });
              return deferred.promise;
            });
            model.initialize(true);
            scope.$apply();
            expect(model.newInstanceSpec.security_groups.length).toBe(1);
            expect(model.newInstanceSpec.security_groups).toEqual(secGroups);
          }
        );

        it('should set a network by default if only one network is available', function () {
          var networks = [ { id: 'net-1', subnets: [ { id: 'subnet1' } ] } ];
          spyOn(neutronApi, 'getNetworks').and.callFake(function () {
            var deferred = $q.defer();
            deferred.resolve({ data: { items: networks } });
            return deferred.promise;
          });
          model.initialize(true);
          scope.$apply();
          expect(model.newInstanceSpec.networks.length).toBe(1);
          expect(model.newInstanceSpec.networks).toEqual(networks);
        });

        it('getPorts at launch should not return child port', function () {
          var ports = [ { id: 'parent',
                          trunk_details:  { trunk_id: 'trunk1',
                                            sub_ports: [ { port_id: 'child' } ] } },
                        { id: 'child' },
                        { id : 'plain' } ];
          var networks = [ { id: 'net-1', subnets: [ { id: 'subnet1' } ] } ];
          spyOn(neutronApi, 'getNetworks').and.callFake(function () {
            var deferred = $q.defer();
            deferred.resolve({ data: { items: networks } });
            return deferred.promise;
          });
          spyOn(neutronApi, 'getPorts').and.callFake(function () {
            var deferred = $q.defer();
            deferred.resolve({ data: { items: ports } });
            return deferred.promise;
          });
          neutronEnabled = true;
          model.initialize(true);
          scope.$apply();
        });

        it('should have the proper entries in allowedBootSources', function() {
          model.initialize(true);
          scope.$apply();

          expect(model.allowedBootSources).toBeDefined();
          expect(model.allowedBootSources.length).toBe(4);
          expect(model.allowedBootSources).toContain(IMAGE);
          expect(model.allowedBootSources).toContain(VOLUME);
          expect(model.allowedBootSources).toContain(VOLUME_SNAPSHOT);
          expect(model.allowedBootSources).toContain(INSTANCE_SNAPSHOT);
        });

        it('should have proper allowedBootSources if settings are missing', function() {
          delete settings.LAUNCH_INSTANCE_DEFAULTS;
          model.initialize(true);
          scope.$apply();

          expect(model.allowedBootSources).toBeDefined();
          expect(model.allowedBootSources.length).toBe(4);
          expect(model.allowedBootSources).toContain(IMAGE);
          expect(model.allowedBootSources).toContain(INSTANCE_SNAPSHOT);
          expect(model.allowedBootSources).toContain(VOLUME);
          expect(model.allowedBootSources).toContain(VOLUME_SNAPSHOT);
        });

        it('should have proper allowedBootSources if specific settings missing', function() {
          delete settings.LAUNCH_INSTANCE_DEFAULTS.create_volume;
          delete settings.LAUNCH_INSTANCE_DEFAULTS.disable_image;
          delete settings.LAUNCH_INSTANCE_DEFAULTS.disable_instance_snapshot;
          delete settings.LAUNCH_INSTANCE_DEFAULTS.disable_volume;
          model.initialize(true);
          scope.$apply();

          expect(model.allowedBootSources).toBeDefined();
          expect(model.allowedBootSources.length).toBe(4);
          expect(model.allowedBootSources).toContain(IMAGE);
          expect(model.allowedBootSources).toContain(INSTANCE_SNAPSHOT);
          expect(model.allowedBootSources).toContain(VOLUME);
          expect(model.allowedBootSources).toContain(VOLUME_SNAPSHOT);
          expect(model.newInstanceSpec.create_volume_default).toBe(true);
        });

        it('should have no images if disable_image is set to true', function() {
          settings.LAUNCH_INSTANCE_DEFAULTS.disable_image = true;
          model.initialize(true);
          scope.$apply();

          expect(model.images.length).toBe(0);
          expect(model.images).toEqual([]);
          expect(model.allowedBootSources).toBeDefined();
          expect(model.allowedBootSources.length).toBe(3);
          expect(model.allowedBootSources).not.toContain(IMAGE);
          expect(model.allowedBootSources).toContain(INSTANCE_SNAPSHOT);
          expect(model.allowedBootSources).toContain(VOLUME);
          expect(model.allowedBootSources).toContain(VOLUME_SNAPSHOT);
        });

        it('should have images if disable_image is missing', function() {
          delete settings.LAUNCH_INSTANCE_DEFAULTS.disable_image;
          model.initialize(true);
          scope.$apply();

          expect(model.allowedBootSources).toBeDefined();
          expect(model.allowedBootSources.length).toBe(4);
          expect(model.allowedBootSources).toContain(IMAGE);
          expect(model.allowedBootSources).toContain(INSTANCE_SNAPSHOT);
          expect(model.allowedBootSources).toContain(VOLUME);
          expect(model.allowedBootSources).toContain(VOLUME_SNAPSHOT);
        });

        it('should have no volumes if disable_volume is set to true', function() {
          settings.LAUNCH_INSTANCE_DEFAULTS.disable_volume = true;
          model.initialize(true);
          scope.$apply();

          expect(model.volumes.length).toBe(0);
          expect(model.volumes).toEqual([]);
          expect(model.volumeSnapshots.length).toBe(2);
          expect(model.volumeSnapshots).toEqual([{ id: 'snap-1', volume_id: 'vol-1' },
                                                 { id: 'snap-2', volume_id: 'vol-2' }]);
          expect(model.allowedBootSources).toBeDefined();
          expect(model.allowedBootSources.length).toBe(3);
          expect(model.allowedBootSources).toContain(IMAGE);
          expect(model.allowedBootSources).toContain(INSTANCE_SNAPSHOT);
          expect(model.allowedBootSources).not.toContain(VOLUME);
          expect(model.allowedBootSources).toContain(VOLUME_SNAPSHOT);
        });

        it('should have volumes if disable_volume is missing', function() {
          delete settings.LAUNCH_INSTANCE_DEFAULTS.disable_volume;
          model.initialize(true);
          scope.$apply();

          expect(model.allowedBootSources).toBeDefined();
          expect(model.allowedBootSources.length).toBe(4);
          expect(model.allowedBootSources).toContain(IMAGE);
          expect(model.allowedBootSources).toContain(INSTANCE_SNAPSHOT);
          expect(model.allowedBootSources).toContain(VOLUME);
          expect(model.allowedBootSources).toContain(VOLUME_SNAPSHOT);
        });

        it('should have volume snapshots if disable_volume_snapshot is missing', function() {
          delete settings.LAUNCH_INSTANCE_DEFAULTS.disable_volume_snapshot;
          model.initialize(true);
          scope.$apply();

          expect(model.allowedBootSources).toBeDefined();
          expect(model.allowedBootSources.length).toBe(4);
          expect(model.allowedBootSources).toContain(IMAGE);
          expect(model.allowedBootSources).toContain(INSTANCE_SNAPSHOT);
          expect(model.allowedBootSources).toContain(VOLUME);
          expect(model.allowedBootSources).toContain(VOLUME_SNAPSHOT);
        });

        it('should not have volume snapshots if disable_volume_snapshot is set to true',
        function() {
          settings.LAUNCH_INSTANCE_DEFAULTS.disable_volume_snapshot = true;
          model.initialize(true);
          scope.$apply();

          expect(model.allowedBootSources).toBeDefined();
          expect(model.allowedBootSources.length).toBe(3);
          expect(model.allowedBootSources).toContain(IMAGE);
          expect(model.allowedBootSources).toContain(INSTANCE_SNAPSHOT);
          expect(model.allowedBootSources).toContain(VOLUME);
          expect(model.allowedBootSources).not.toContain(VOLUME_SNAPSHOT);
        });

        it('should have no snapshot if disable_instance_snapshot is set to true', function() {
          settings.LAUNCH_INSTANCE_DEFAULTS.disable_instance_snapshot = true;
          model.initialize(true);
          scope.$apply();

          expect(model.allowedBootSources).toBeDefined();
          expect(model.allowedBootSources.length).toBe(3);
          expect(model.allowedBootSources).toContain(IMAGE);
          expect(model.allowedBootSources).not.toContain(INSTANCE_SNAPSHOT);
          expect(model.allowedBootSources).toContain(VOLUME);
          expect(model.allowedBootSources).toContain(VOLUME_SNAPSHOT);
        });

        it('should have snapshot if disable_instance_snapshot is missing', function() {
          delete settings.LAUNCH_INSTANCE_DEFAULTS.disable_instance_snapshot;
          model.initialize(true);
          scope.$apply();

          expect(model.allowedBootSources).toBeDefined();
          expect(model.allowedBootSources.length).toBe(4);
          expect(model.allowedBootSources).toContain(IMAGE);
          expect(model.allowedBootSources).toContain(INSTANCE_SNAPSHOT);
          expect(model.allowedBootSources).toContain(VOLUME);
          expect(model.allowedBootSources).toContain(VOLUME_SNAPSHOT);
        });

        it('should have no snapshot and no image if both are disabled', function() {
          settings.LAUNCH_INSTANCE_DEFAULTS.disable_image = true;
          settings.LAUNCH_INSTANCE_DEFAULTS.disable_instance_snapshot = true;

          model.initialize(true);
          scope.$apply();

          expect(model.allowedBootSources).toBeDefined();
          expect(model.allowedBootSources.length).toBe(2);
          expect(model.allowedBootSources).not.toContain(IMAGE);
          expect(model.allowedBootSources).not.toContain(INSTANCE_SNAPSHOT);
          expect(model.allowedBootSources).toContain(VOLUME);
          expect(model.allowedBootSources).toContain(VOLUME_SNAPSHOT);
        });

        it('should have snapshot and image if both are missing', function() {
          delete settings.LAUNCH_INSTANCE_DEFAULTS.disable_image;
          delete settings.LAUNCH_INSTANCE_DEFAULTS.disable_instance_snapshot;

          model.initialize(true);
          scope.$apply();

          expect(model.allowedBootSources).toBeDefined();
          expect(model.allowedBootSources.length).toBe(4);
          expect(model.allowedBootSources).toContain(IMAGE);
          expect(model.allowedBootSources).toContain(INSTANCE_SNAPSHOT);
          expect(model.allowedBootSources).toContain(VOLUME);
          expect(model.allowedBootSources).toContain(VOLUME_SNAPSHOT);
        });

        it('should have maxTotalVolumes and maxTotalVolumeGigabytes if cinder ' +
           'is enabled', function() {
          cinderEnabled = true;
          model.initialize(true);
          scope.$apply();

          expect(model.cinderLimits.maxTotalVolumes).toBe(100);
          expect(model.cinderLimits.maxTotalVolumeGigabytes).toBe(1000);
        });

        it('should not fetch server groups if the policy does not allow it', function () {
          ifAllowedResolve = false;
          model.initialize(true);
          scope.$apply();
          expect(novaApi.getServerGroups.calls.count()).toBe(0);
        });

        it('should fetch server groups if the policy allows it', function () {
          ifAllowedResolve = true;
          model.initialize(true);
          scope.$apply();
          expect(novaApi.getServerGroups.calls.count()).toBe(1);
        });
      });

      describe('Post Initialization Model - Initializing', function() {

        beforeEach(function() {
          model.initializing = true;
          model.initialize(true);  // value and return don't matter
        });

        // This is here to ensure that as people add/change items, they
        // don't forget to implement tests for them.
        it('has the right number of properties', function() {
          expect(Object.keys(model.newInstanceSpec).length).toBe(22);
        });

        it('sets availability zone to null', function() {
          expect(model.newInstanceSpec.availability_zone).toBeNull();
        });

        it('sets admin pass to null', function() {
          expect(model.newInstanceSpec.admin_pass).toBeNull();
        });

        it('sets description to null', function() {
          expect(model.newInstanceSpec.description).toBeNull();
        });

        it('sets config drive to false', function() {
          expect(model.newInstanceSpec.config_drive).toBe(false);
        });

        it('sets create volume to true', function() {
          expect(model.newInstanceSpec.create_volume_default).toBe(true);
        });

        it('sets user data to an empty string', function() {
          expect(model.newInstanceSpec.user_data).toBe('');
        });

        it('sets disk config to AUTO', function() {
          expect(model.newInstanceSpec.disk_config).toBe('AUTO');
        });

        it('sets flavor to be null', function() {
          expect(model.newInstanceSpec.flavor).toBeNull();
        });

        it('sets instance count to 1', function() {
          expect(model.newInstanceSpec.instance_count).toBe(1);
        });

        it('sets key pair to an empty array', function() {
          expect(model.newInstanceSpec.key_pair).toEqual([]);
        });

        it('sets name to null', function() {
          expect(model.newInstanceSpec.name).toBeNull();
        });

        it('sets networks to an empty array', function() {
          expect(model.newInstanceSpec.networks).toEqual([]);
        });

        it('sets ports to an empty array', function() {
          expect(model.newInstanceSpec.ports).toEqual([]);
        });

        it('sets security groups to an empty array', function() {
          expect(model.newInstanceSpec.security_groups).toEqual([]);
        });

        it('sets scheduler hints to an empty object', function() {
          expect(model.newInstanceSpec.scheduler_hints).toEqual({});
        });

        it('sets source type to null', function() {
          expect(model.newInstanceSpec.source_type).toBeNull();
        });

        it('sets source to an empty array', function() {
          expect(model.newInstanceSpec.source).toEqual([]);
        });

        it('sets volume options appropriately', function() {
          expect(model.newInstanceSpec.vol_create).toBe(false);
          expect(model.newInstanceSpec.vol_delete_on_instance_delete).toBe(false);
          expect(model.newInstanceSpec.vol_size).toBe(1);
        });

      });

      describe('Create Instance', function() {
        var metadata, hints;

        beforeEach(function() {
          // initialize some data
          model.newInstanceSpec.source_type = { type: 'image' };
          model.newInstanceSpec.source = [ { id: 'cirros' } ];
          model.newInstanceSpec.flavor = { id: 'm1.tiny' };
          model.newInstanceSpec.networks = [ { id: 'public' }, { id: 'private' } ];
          model.newInstanceSpec.ports = [ ];
          model.newInstanceSpec.key_pair = [ { name: 'keypair1' } ];
          model.newInstanceSpec.security_groups = [ { id: 'adminId', name: 'admin' },
                                                    { id: 'demoId', name: 'demo' } ];
          model.newInstanceSpec.scheduler_hints = {};
          model.newInstanceSpec.vol_create = true;
          model.newInstanceSpec.vol_delete_on_instance_delete = true;
          model.newInstanceSpec.vol_size = 10;
          model.newInstanceSpec.server_groups = [];

          metadata = {'foo': 'bar'};
          model.metadataTree = {
            getExisting: function() {
              return metadata;
            }
          };

          hints = {'hint1': 'val1'};
          model.hintsTree = {
            getExisting: function() {
              return hints;
            }
          };
        });

        it('should set final spec in format required by Nova (Neutron disabled)', function() {
          var finalSpec = model.createInstance();
          var finalNetworks = [
            { 'net-id': 'public', 'v4-fixed-ip': '' },
            { 'net-id': 'private', 'v4-fixed-ip': '' }
          ];

          expect(finalSpec.source_id).toBe(null);
          expect(finalSpec.flavor_id).toBe('m1.tiny');
          expect(finalSpec.nics).toEqual(finalNetworks);
          expect(finalSpec.key_name).toBe('keypair1');
          expect(finalSpec.security_groups).toEqual([ 'admin', 'demo' ]);
        });

        it('should set final spec in format required for Block Device Mapping v2', function() {
          var finalSpec = model.createInstance();
          var expectedBlockDevice = [{
            source_type: 'image',
            destination_type: 'volume',
            delete_on_termination: true,
            uuid: 'cirros',
            boot_index: '0',
            volume_size: 10
          }];

          expect(finalSpec.block_device_mapping_v2).toEqual(expectedBlockDevice);
        });

        it('should set final security groups using name when Neutron enabled', function() {
          model.neutronEnabled = true;
          var finalSpec = model.createInstance();

          expect(finalSpec.security_groups).toEqual([ 'adminId', 'demoId' ]);
        });

        it('should remove flavor from final spec if flavor was null', function() {
          model.newInstanceSpec.flavor = null;

          var finalSpec = model.createInstance();
          expect(finalSpec.flavor_id).toBeUndefined();
        });

        it('should handle source type of "volume"', function() {
          model.newInstanceSpec.source_type.type = 'volume';
          model.newInstanceSpec.source[0].id = 'imAnID';
          model.newInstanceSpec.vol_delete_on_instance_delete = 'yep';

          var finalSpec = model.createInstance();
          expect(finalSpec.source_id).toBe('');
        });

        it('should handle source type of "snapshot"', function() {
          model.newInstanceSpec.source_type.type = 'snapshot';
          model.newInstanceSpec.source[0].id = 'imAnID';

          var finalSpec = model.createInstance();
          var expectedBlockDevice = [{
            source_type: 'image',
            destination_type: 'volume',
            delete_on_termination: true,
            uuid: 'imAnID',
            boot_index: '0',
            volume_size: 10
          }];

          expect(finalSpec.block_device_mapping_v2).toEqual(expectedBlockDevice);
        });

        it('should handle source type of "volume_snapshot"', function() {
          model.newInstanceSpec.source_type.type = 'volume_snapshot';
          model.newInstanceSpec.source[0].id = 'imAnID';
          model.newInstanceSpec.vol_delete_on_instance_delete = 'yep';

          var finalSpec = model.createInstance();
          expect(finalSpec.source_id).toBe('');
        });

        it('should process source_id if unknown type', function() {
          model.newInstanceSpec.source_type.type = 'unknown';
          model.newInstanceSpec.source[0].id = 'imAnID';

          var finalSpec = model.createInstance();
          expect(finalSpec.source_id).toBe('imAnID');
        });

        it('should not create block device mappings if not creating a volume', function() {
          model.newInstanceSpec.source_type.type = 'image';
          model.newInstanceSpec.vol_create = false;

          var finalSpec = model.createInstance();
          expect(finalSpec.block_device_mapping_v2).toBeUndefined();
        });

        it('sets a null key name & removes keypair if no key pair presented', function() {
          model.newInstanceSpec.key_pair = [];

          var finalSpec = model.createInstance();
          expect(finalSpec.key_name).toBeNull();
          expect(finalSpec.key_pair).toBeUndefined();
        });

        it('leaves the key name and removes keypair property if no key pair presented', function() {
          model.newInstanceSpec.key_pair = [];
          model.newInstanceSpec.key_name = 'Jerry';

          var finalSpec = model.createInstance();
          expect(finalSpec.key_name).toBe('Jerry');
          expect(finalSpec.key_pair).toBeUndefined();
        });

        it('stips null properties', function() {
          model.newInstanceSpec.useless = null;

          var finalSpec = model.createInstance();
          expect(finalSpec.useless).toBeUndefined();
        });

        it('should set final spec in format required if ports are used', function() {
          model.newInstanceSpec.ports = [{id: 'port1'}];

          var finalSpec = model.createInstance();
          var finalNetworks = [
            { 'net-id': 'public', 'v4-fixed-ip': '' },
            { 'net-id': 'private', 'v4-fixed-ip': '' },
            { 'port-id': 'port1' }
          ];

          expect(finalSpec.nics).toEqual(finalNetworks);
        });

        it('should not have meta property if no metadata specified', function() {
          metadata = {};

          var finalSpec = model.createInstance();
          expect(finalSpec.meta).toBeUndefined();

          model.metadataTree = null;

          finalSpec = model.createInstance();
          expect(finalSpec.meta).toBeUndefined();
        });

        it('should have meta property if metadata specified', function() {
          var finalSpec = model.createInstance();
          expect(finalSpec.meta).toBe(metadata);
        });

        it('should have only group for scheduler_hints if no other hints specified', function() {
          hints = {};
          model.newInstanceSpec.server_groups = [{'id': 'group1'}];
          var finalHints = {'group': model.newInstanceSpec.server_groups[0].id};

          var finalSpec = model.createInstance();
          expect(finalSpec.scheduler_hints).toEqual(finalHints);

          model.hintsTree = null;

          finalSpec = model.createInstance();
          expect(finalSpec.scheduler_hints).toEqual(finalHints);
        });

        it('should have scheduler_hints property if scheduler hints specified', function() {
          var finalHints = hints;
          finalHints.group = 'group1';

          var finalSpec = model.createInstance();
          expect(finalSpec.scheduler_hints).toEqual(finalHints);
        });

        it('should have no scheduler_hints if no scheduler hints specified', function() {
          hints = {};
          model.newInstanceSpec.server_groups = [];

          var finalSpec = model.createInstance();
          expect(finalSpec.scheduler_hints).toEqual({});
        });

      });
    });
  });
})();
