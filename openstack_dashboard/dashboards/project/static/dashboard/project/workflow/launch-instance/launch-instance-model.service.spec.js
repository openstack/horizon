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
      var model, scope, $q;
      var cinderEnabled = false;
      var neutronEnabled = false;
      var novaExtensionsEnabled = false;

      beforeEach(module('horizon.dashboard.project.workflow.launch-instance'));

      beforeEach(module(function($provide) {
        $provide.value('horizon.app.core.openstack-service-api.glance', {
          getImages: function() {
            var images = [
              { container_format: 'aki', properties: {} },
              { container_format: 'ari', properties: {} },
              { container_format: 'ami', properties: {} },
              { container_format: 'raw', properties: {} },
              { container_format: 'ami', properties: { image_type: 'snapshot' } },
              { container_format: 'raw', properties: { image_type: 'snapshot' } }
            ];

            var deferred = $q.defer();
            deferred.resolve({ data: { items: images } });

            return deferred.promise;
          },
          getNamespaces: function() {
            var namespaces = [ 'ns-1', 'ns-2' ];

            var deferred = $q.defer();
            deferred.resolve({ data: { items: namespaces } });

            return deferred.promise;
          }
        });

        $provide.value('horizon.app.core.openstack-service-api.nova', {
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
          }
        });

        $provide.value('horizon.app.core.openstack-service-api.security-group', {
          query: function() {
            var secGroups = [
              { name: 'security-group-1' },
              { name: 'security-group-2' }
            ];

            var deferred = $q.defer();
            deferred.resolve({ data: { items: secGroups } });

            return deferred.promise;
          }
        });

        $provide.value('horizon.app.core.openstack-service-api.neutron', {
          getNetworks: function() {
            var networks = [ { id: 'net-1' }, { id: 'net-2' } ];

            var deferred = $q.defer();
            deferred.resolve({ data: { items: networks } });

            return deferred.promise;
          }
        });

        $provide.value('horizon.app.core.openstack-service-api.cinder', {
          getVolumes: function() {
            var volumes = [ { id: 'vol-1' }, { id: 'vol-2' } ];

            var deferred = $q.defer();
            deferred.resolve({ data: { items: volumes } });

            return deferred.promise;
          },
          getVolumeSnapshots: function() {
            var snapshots = [ { id: 'snap-1' }, { id: 'snap-2' } ];

            var deferred = $q.defer();
            deferred.resolve({ data: { items: snapshots } });

            return deferred.promise;
          }
        });

        $provide.value('horizon.app.core.openstack-service-api.serviceCatalog', {
          ifTypeEnabled: function(theType) {
            var deferred = $q.defer();

            if (theType === 'network' && neutronEnabled) {
              deferred.resolve();
            } else if (theType === 'volume' && cinderEnabled) {
              deferred.resolve();
            } else {
              deferred.reject();
            }

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

        $provide.value('horizon.framework.widgets.toast.service', {
          add: function() {}
        });
      }));

      beforeEach(inject(function(launchInstanceModel, $rootScope, _$q_) {
        model = launchInstanceModel;
        $q = _$q_;
        scope = $rootScope.$new();
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
            'profiles', 'securityGroups', 'volumes', 'volumeSnapshots'];

          datasets.forEach(function(name) {
            expect(model[name]).toEqual([]);
          });
        });

        it('initialized metadatadefs to null values', function() {
          expect(model.metadataDefs.flavor).toBeNull();
          expect(model.metadataDefs.image).toBeNull();
          expect(model.metadataDefs.volume).toBeNull();
          expect(model.metadataDefs.instance).toBeNull();
          expect(Object.keys(model.metadataDefs).length).toBe(4);
        });

        it('defaults "allow create volume from image" to false', function() {
          expect(model.allowCreateVolumeFromImage).toBe(false);
        });

        it('defaults "are port profiles supported" to false', function() {
          expect(model.arePortProfilesSupported).toBe(false);
        });

        it('defaults "volume bootable" to false', function() {
          expect(model.volumeBootable).toBe(false);
        });

        it('defaults "metadataTree" to null', function() {
          expect(model.metadataTree).toBe(null);
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

          expect(model.images.length).toBe(2);
          expect(model.imageSnapshots.length).toBe(2);
          expect(model.availabilityZones.length).toBe(2);
          expect(model.flavors.length).toBe(2);
          expect(model.keypairs.length).toBe(2);
          expect(model.securityGroups.length).toBe(2);
          expect(model.novaLimits.maxTotalInstances).toBe(10);
          expect(model.novaLimits.totalInstancesUsed).toBe(0);
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
      });

      describe('Post Initialization Model - Initializing', function() {

        beforeEach(function() {
          model.initializing = true;
          model.initialize(true);  // value and return don't matter
        });

        // This is here to ensure that as people add/change items, they
        // don't forget to implement tests for them.
        it('has the right number of properties', function() {
          expect(Object.keys(model.newInstanceSpec).length).toBe(18);
        });

        it('sets availability zone to null', function() {
          expect(model.newInstanceSpec.availability_zone).toBeNull();
        });

        it('sets admin pass to null', function() {
          expect(model.newInstanceSpec.admin_pass).toBeNull();
        });

        it('sets config drive to false', function() {
          expect(model.newInstanceSpec.config_drive).toBe(false);
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

        it('sets profile to an empty object', function() {
          expect(model.newInstanceSpec.profile).toEqual({});
        });

        it('sets security groups to an empty array', function() {
          expect(model.newInstanceSpec.security_groups).toEqual([]);
        });

        it('sets source type to null', function() {
          expect(model.newInstanceSpec.source_type).toBeNull();
        });

        it('sets source to an empty array', function() {
          expect(model.newInstanceSpec.source).toEqual([]);
        });

        it('sets volume options appropriately', function() {
          expect(model.newInstanceSpec.vol_create).toBe(false);
          expect(model.newInstanceSpec.vol_device_name).toBe('vda');
          expect(model.newInstanceSpec.vol_delete_on_instance_delete).toBe(false);
          expect(model.newInstanceSpec.vol_size).toBe(1);
        });

      });

      describe('Create Instance', function() {
        var metadata;

        beforeEach(function() {
          // initialize some data
          model.newInstanceSpec.source_type = { type: 'image' };
          model.newInstanceSpec.source = [ { id: 'cirros' } ];
          model.newInstanceSpec.flavor = { id: 'm1.tiny' };
          model.newInstanceSpec.networks = [ { id: 'public' }, { id: 'private' } ];
          model.newInstanceSpec.key_pair = [ { name: 'keypair1' } ];
          model.newInstanceSpec.security_groups = [ { id: 'adminId', name: 'admin' },
                                                    { id: 'demoId', name: 'demo' } ];
          model.newInstanceSpec.vol_create = true;
          model.newInstanceSpec.vol_delete_on_instance_delete = true;
          model.newInstanceSpec.vol_device_name = "volTestName";
          model.newInstanceSpec.vol_size = 10;

          metadata = {'foo': 'bar'};
          model.metadataTree = {
            getExisting: function() {
              return metadata;
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
            device_name: 'volTestName',
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
          expect(finalSpec.block_device_mapping.volTestName)
            .toBe('imAnID:vol::yep');
          expect(finalSpec.source_id).toBe('');
        });

        it('should handle source type of "snapshot"', function() {
          model.newInstanceSpec.source_type.type = 'snapshot';
          model.newInstanceSpec.source[0].id = 'imAnID';

          var finalSpec = model.createInstance();
          expect(finalSpec.source_id).toBe('imAnID');
        });

        it('should handle source type of "volume_snapshot"', function() {
          model.newInstanceSpec.source_type.type = 'volume_snapshot';
          model.newInstanceSpec.source[0].id = 'imAnID';
          model.newInstanceSpec.vol_delete_on_instance_delete = 'yep';

          var finalSpec = model.createInstance();
          expect(finalSpec.block_device_mapping.volTestName)
            .toBe('imAnID:snap::yep');
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

        it('provides null for device_name when falsy', function() {
          model.newInstanceSpec.source_type.type = 'image';
          model.newInstanceSpec.vol_device_name = false;
          model.newInstanceSpec.vol_create = true;

          var finalSpec = model.createInstance();
          expect(finalSpec.block_device_mapping_v2[0].device_name).toBeNull();
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

      });
    });
  });
})();
