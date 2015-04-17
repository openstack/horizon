(function () {
  'use strict';

  var push = Array.prototype.push,
      noop = angular.noop;

  /**
   * @ngdoc overview
   * @name hz.dashboard.launch-instance
   *
   * @description
   * Manage workflow of creating server.
   */

  var module = angular.module('hz.dashboard.launch-instance');

  /**
   * @ngdoc service
   * @name launchInstanceModel
   *
   * @description
   * This is the M part in MVC design pattern for launch instance
   * wizard workflow. It is responsible for providing data to the
   * view of each step in launch instance workflow and collecting
   * user's input from view for  creation of new instance.  It is
   * also the center point of communication between launch instance
   * UI and services API.
   */

  module.factory('launchInstanceModel', ['$q',
    'cinderAPI',
    'glanceAPI',
    'keystoneAPI',
    'neutronAPI',
    'novaAPI',
    'novaExtensions',
    'securityGroup',
    'serviceCatalog',

    function ($q,
              cinderAPI,
              glanceAPI,
              keystoneAPI,
              neutronAPI,
              novaAPI,
              novaExtensions,
              securityGroup,
              serviceCatalog) {

      var initPromise,
          allNamespacesPromise;

      // Constants (const in ES6)
      var NON_BOOTABLE_IMAGE_TYPES = ['aki', 'ari'],
          SOURCE_TYPE_IMAGE = 'image',
          SOURCE_TYPE_SNAPSHOT = 'snapshot',
          SOURCE_TYPE_VOLUME = 'volume',
          SOURCE_TYPE_VOLUME_SNAPSHOT = 'volume_snapshot';

      /**
       * @ngdoc model api object
       */
      var model = {

        initializing: false,
        initialized: false,


        /**
         * @name newInstanceSpec
         *
         * @description
         * A dictionary like object containing specification collected from user's
         * input.  Its required properties include:
         *
         * @property {String} name: The new server name.
         * @property {String} source_type: The type of source
         *   Valid options: (image | snapshot | volume | volume_snapshot)
         * @property {String} source_id: The ID of the image / volume to use.
         * @property {String} flavor_id: The ID of the flavor to use.
         *
         * Other parameters are accepted as per the underlying novaclient:
         *  - https://github.com/openstack/python-novaclient/blob/master/novaclient/v2/servers.py#L417
         * But may be required additional values as per nova:
         *  - https://github.com/openstack/horizon/blob/master/openstack_dashboard/api/rest/nova.py#L127
         *
         * The JS code only needs to set the values below as they are made.
         * The createInstance function will map them appropriately.
         */

        // see initializeNewInstanceSpec
        newInstanceSpec: {},

        /**
         * cloud service properties, they should be READ-ONLY to all UI controllers
         */

        availabilityZones: [],
        flavors: [],
        allowedBootSources: [],
        images: [],
        allowCreateVolumeFromImage: false,
        arePortProfilesSupported: false,
        imageSnapshots: [],
        keypairs: [],
        metadataDefs: {
          flavor: null,
          image: null,
          volume: null
        },
        networks: [],
        neutronEnabled: false,
        novaLimits: {},
        profiles: [],
        securityGroups: [],
        volumeBootable: false,
        volumes: [],
        volumeSnapshots: [],

        /**
         * api methods for UI controllers
         */

        initialize: initialize,
        createInstance: createInstance
      };

      // Local function.
      function initializeNewInstanceSpec(){

        model.newInstanceSpec = {
          availability_zone: null,
          admin_pass: null,
          config_drive: false,
          user_data: '',                  // REQUIRED Server Key.  Null allowed.
          disk_config: 'AUTO',
          flavor: null,                   // REQUIRED
          instance_count: 1,
          key_pair: [],                   // REQUIRED Server Key
          name: null,                     // REQUIRED
          networks: [],
          profile: {},
          security_groups: [],            // REQUIRED Server Key. May be empty.
          source_type: null,              // REQUIRED for JS logic (image | snapshot | volume | volume_snapshot)
          source: [],
          vol_create: false,              // REQUIRED for JS logic
          vol_device_name: 'vda',         // May be null
          vol_delete_on_terminate: false,
          vol_size: 1
        };
      }

      /**
       * @ngdoc method
       * @name launchInstanceModel.initialize
       * @returns {promise}
       *
       * @description
       * Send request to get all data to initialize the model.
       */

      function initialize(deep) {
        var deferred, promise;

        // Each time opening launch instance wizard, we need to do this, or
        // we can call the whole methods `reset` instead of `initialize`.
        initializeNewInstanceSpec();

        if (model.initializing) {
          promise = initPromise;

        } else if (model.initialized && !deep) {
          deferred = $q.defer();
          promise = deferred.promise;
          deferred.resolve();

        } else {
          model.initializing = true;

          model.allowedBootSources.length = 0;

          promise = $q.all([
            getImages(),
            novaAPI.getAvailabilityZones().then(onGetAvailabilityZones, noop),
            novaAPI.getFlavors(true, true).then(onGetFlavors, noop),
            novaAPI.getKeypairs().then(onGetKeypairs, noop),
            novaAPI.getLimits().then(onGetNovaLimits, noop),
            securityGroup.query().then(onGetSecurityGroups, noop),
            serviceCatalog.ifTypeEnabled('network').then(getNetworks, noop),
            serviceCatalog.ifTypeEnabled('volume').then(getVolumes, noop)
          ]);

          promise.then(
            function() {
              model.initializing = false;
              model.initialized = true;
              // This provides supplemental data non-critical to launching
              // an instance.  Therefore we load it only if the critical data
              // all loads successfully.
              getMetadataDefinitions();
            },
            function () {
              model.initializing = false;
              model.initialized = false;
            }
          );
        }

        return promise;
      }

      /**
       * @ngdoc method
       * @name launchInstanceModel.createInstance
       * @returns {promise}
       *
       * @description
       * Send request for creating server.
       */

      function createInstance() {
        var finalSpec = angular.copy(model.newInstanceSpec);

        cleanNullProperties();

        setFinalSpecBootsource(finalSpec);
        setFinalSpecFlavor(finalSpec);
        setFinalSpecNetworks(finalSpec);
        setFinalSpecKeyPairs(finalSpec);
        setFinalSpecSecurityGroups(finalSpec);

        return novaAPI.createServer(finalSpec);
      }

      function cleanNullProperties(finalSpec){
        // Initially clean fields that don't have any value.
        for (var key in finalSpec) {
          if (finalSpec.hasOwnProperty(key)  && finalSpec[key] === null) {
            delete finalSpec[key];
          }
        }
      }

      //
      // Local
      //

      function onGetAvailabilityZones(data) {
        model.availabilityZones.length = 0;
        push.apply(model.availabilityZones, data.data.items
          .filter(function (zone) {
            return zone.zoneState && zone.zoneState.available;
          })
          .map(function (zone) {
            return zone.zoneName;
          })
        );

        if(model.availabilityZones.length > 0) {
          model.newInstanceSpec.availability_zone = model.availabilityZones[0];
        }
      }

      // Flavors

      function onGetFlavors(data) {
        model.flavors.length = 0;
        push.apply(model.flavors, data.data.items);
      }

      function setFinalSpecFlavor(finalSpec) {
        if ( finalSpec.flavor ) {
          finalSpec.flavor_id = finalSpec.flavor.id;
        } else {
          delete finalSpec.flavor_id;
        }

        delete finalSpec.flavor;
      }

      // Keypairs

      function onGetKeypairs(data) {
        angular.extend(
          model.keypairs,
          data.data.items.map(function (e) {
            e.keypair.id = e.keypair.name;
            return e.keypair;
          }));
      }

      function setFinalSpecKeyPairs(finalSpec) {
        // Nova only wants the key name. It is a required field, even if None.
        if(!finalSpec.key_name && finalSpec.key_pair.length === 1){
          finalSpec.key_name = finalSpec.key_pair[0].name;
        } else if (!finalSpec.key_name) {
          finalSpec.key_name = null;
        }

        delete finalSpec.key_pair;
      }

      // Security Groups

      function onGetSecurityGroups(data) {
        model.securityGroups.length = 0;
        push.apply(model.securityGroups, data.data.items);
        // set initial default
        if (model.newInstanceSpec.security_groups.length === 0 &&
            model.securityGroups.length > 0) {
          model.securityGroups.forEach(function (securityGroup) {
            if (securityGroup.name === 'default') {
              model.newInstanceSpec.security_groups.push(securityGroup);
            }
          });
        }
      }

      function setFinalSpecSecurityGroups(finalSpec) {
        // pull out the ids from the security groups objects
        var security_group_ids = [];
        finalSpec.security_groups.forEach(function(securityGroup){
          if(model.neutronEnabled) {
            security_group_ids.push(securityGroup.id);
          } else {
            security_group_ids.push(securityGroup.name);
          }
        });
        finalSpec.security_groups = security_group_ids;
      }

      // Networks

      function getNetworks() {
        return neutronAPI.getNetworks().then(onGetNetworks, noop);
      }

      function onGetNetworks(data) {
        model.neutronEnabled = true;
        model.networks.length = 0;
        push.apply(model.networks, data.data.items);
      }

      function setFinalSpecNetworks(finalSpec) {
        finalSpec.nics = [];
        finalSpec.networks.forEach(function (network) {
          finalSpec.nics.push(
            {
              "net-id": network.id,
              "v4-fixed-ip": ""
            });
        });
        delete finalSpec.networks;
      }

      // Boot Source

      function getImages(){
        return glanceAPI.getImages({status:'active'}).then(onGetImages);
      }

      function isBootableImageType(image){
        // This is a blacklist of images that can not be booted.
        // If the image container type is in the blacklist
        // The evaluation will result in a 0 or greater index.
        return NON_BOOTABLE_IMAGE_TYPES.indexOf(image.container_format) < 0;
      }

      function onGetImages(data) {
        model.images.length = 0;
        push.apply(model.images, data.data.items.filter(function (image) {
          return isBootableImageType(image) &&
            (!image.properties || image.properties.image_type !== 'snapshot');
        }));
        addAllowedBootSource(model.images, SOURCE_TYPE_IMAGE, gettext('Image'));

        model.imageSnapshots.length = 0;
        push.apply(model.imageSnapshots,data.data.items.filter(function (image) {
          return isBootableImageType(image) &&
            (image.properties && image.properties.image_type === 'snapshot');
        }));

        addAllowedBootSource(model.imageSnapshots, SOURCE_TYPE_SNAPSHOT, gettext('Instance Snapshot'));
      }

      function getVolumes(){
        var volumePromises = [];
        // Need to check if Volume service is enabled before getting volumes
        model.volumeBootable = true;
        addAllowedBootSource(model.volumes, SOURCE_TYPE_VOLUME, gettext('Volume'));
        addAllowedBootSource(model.volumeSnapshots, SOURCE_TYPE_VOLUME_SNAPSHOT, gettext('Volume Snapshot'));
        volumePromises.push(cinderAPI.getVolumes({ status: 'available',  bootable: 1 }).then(onGetVolumes));
        volumePromises.push(cinderAPI.getVolumeSnapshots({ status: 'available' }).then(onGetVolumeSnapshots));

        // Can only boot image to volume if the Nova extension is enabled.
        novaExtensions.ifNameEnabled('BlockDeviceMappingV2Boot')
          .then(function(){ model.allowCreateVolumeFromImage = true; });

        return $q.all(volumePromises);
      }

      function onGetVolumes(data) {
        model.volumes.length = 0;
        push.apply(model.volumes, data.data.items);
      }

      function onGetVolumeSnapshots(data) {
        model.volumeSnapshots.length = 0;
        push.apply(model.volumeSnapshots, data.data.items);
      }

      function addAllowedBootSource(rawTypes, type, label) {
        if (rawTypes && rawTypes.length > 0) {
          model.allowedBootSources.push({
            type: type,
            label: label
          });
        }
      }

      function setFinalSpecBootsource(finalSpec) {
        finalSpec.source_id = finalSpec.source && finalSpec.source[0] && finalSpec.source[0].id;
        delete finalSpec.source;

        switch (finalSpec.source_type.type) {
          case SOURCE_TYPE_IMAGE:
            setFinalSpecBootImageToVolume(finalSpec);
            break;
          case SOURCE_TYPE_SNAPSHOT:
            break;
          case SOURCE_TYPE_VOLUME:
            setFinalSpecBootFromVolumeDevice(finalSpec, 'vol');
            break;
          case SOURCE_TYPE_VOLUME_SNAPSHOT:
            setFinalSpecBootFromVolumeDevice(finalSpec, 'snap');
            break;
          default:
            // error condition
            console.log("Unknown source type: " + finalSpec.source_type);
        }

        // The following are all fields gathered into simple fields by
        // steps so that the view can simply bind to simple model attributes
        // that are then transformed a single time to Nova's expectation
        // at launch time.
        delete finalSpec.source_type;
        delete finalSpec.vol_create;
        delete finalSpec.vol_device_name;
        delete finalSpec.vol_delete_on_terminate;
        delete finalSpec.vol_size;
      }

      function setFinalSpecBootImageToVolume(finalSpec){
        if(finalSpec.vol_create) {
          // Specify null to get Autoselection (not empty string)
          var device_name = finalSpec.vol_device_name ? finalSpec.vol_device_name : null;
          finalSpec.block_device_mapping_v2 = [];
          finalSpec.block_device_mapping_v2.push(
            {
              'device_name': device_name,
              'source_type': SOURCE_TYPE_IMAGE,
              'destination_type': SOURCE_TYPE_VOLUME,
              'delete_on_termination': finalSpec.vol_delete_on_terminate ? 1 : 0,
              'uuid': finalSpec.source_id,
              'boot_index': '0',
              'volume_size': finalSpec.vol_size
            }
          );
        }
      }

      function setFinalSpecBootFromVolumeDevice(finalSpec, sourceType) {
        finalSpec.block_device_mapping = {};
        finalSpec.block_device_mapping[finalSpec.vol_device_name] = [
            finalSpec.source_id,
            ':',
            sourceType,
            '::',
            (finalSpec.vol_delete_on_terminate ? 1 : 0)
          ].join('');

        // Source ID must be empty for API
        finalSpec.source_id = '';
      }

      // Nova Limits

      function onGetNovaLimits(data) {
        angular.extend(model.novaLimits, data.data);
      }

      // Metadata Definitions

      /**
       * Metadata definitions provide supplemental information in detail
       * rows and should not slow down any of the other load processes.
       * All code should be written to treat metadata definitions as
       * optional, because they are never guaranteed to exist.
       */
      function getMetadataDefinitions() {
        // Metadata definitions often apply to multiple
        // resource types. It is optimal to make a single
        // request for all desired resource types.
        var resourceTypes = {
          flavor: 'OS::Nova::Flavor',
          image: 'OS::Glance::Image',
          volume: 'OS::Cinder::Volumes'
        };

        angular.forEach(resourceTypes, function (resourceType, key) {
          glanceAPI.getNamespaces({
            'resource_type': resourceType
          }, true)
          .then(function (data) {
            var namespaces = data.data.items;
            // This will ensure that the metaDefs model object remains
            // unchanged until metadefs are fully loaded. Otherwise,
            // partial results are loaded and can result in some odd
            // display behavior.
            if(namespaces.length) {
              model.metadataDefs[key] = namespaces;
            }
          });
        });
      }

      return model;
     }
  ]);

})();
