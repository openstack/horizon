/*
 * Copyright 2015 IBM Corp.
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 * http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */
(function () {
  'use strict';

  /**
   * @ngdoc controller
   * @name LaunchInstanceSourceController
   * @description
   * The `LaunchInstanceSourceController` controller provides functions for
   * configuring the source step of the Launch Instance Wizard.
   *
   */
  var push = [].push;

  angular
    .module('horizon.dashboard.project.workflow.launch-instance')
    .controller('LaunchInstanceSourceController', LaunchInstanceSourceController);

  LaunchInstanceSourceController.$inject = [
    '$scope',
    'horizon.dashboard.project.workflow.launch-instance.boot-source-types',
    'horizon.dashboard.project.workflow.launch-instance.basePath',
    'horizon.framework.widgets.transfer-table.events',
    'horizon.framework.widgets.magic-search.events'
  ];

  function LaunchInstanceSourceController($scope,
    bootSourceTypes,
    basePath,
    events,
    magicSearchEvents
  ) {

    var ctrl = this;
    ctrl.volumeSizeError = gettext('Volume size is required and must be an integer');

    // Error text for invalid fields
    /*eslint-disable max-len */
    ctrl.bootSourceTypeError = gettext('Volumes can only be attached to 1 active instance at a time. Please either set your instance count to 1 or select a different source type.');
    /*eslint-enable max-len */

    // toggle button label/value defaults
    ctrl.toggleButtonOptions = [
      { label: gettext('Yes'), value: true },
      { label: gettext('No'), value: false }
    ];

    /*
     * Boot Sources
     */
    ctrl.updateBootSourceSelection = updateBootSourceSelection;
    var selection = ctrl.selection = $scope.model.newInstanceSpec.source;

    /*
     * Transfer table
     */
    ctrl.tableData = {
      available: [],
      allocated: selection,
      displayedAvailable: [],
      displayedAllocated: []
    };
    ctrl.helpText = {};

    ctrl.availableTableConfig = {
      selectAll: false,
      trackId: 'id',
      detailsTemplateUrl: basePath + 'source/source-details.html',
      columns: []
    };

    ctrl.allocatedTableConfig = angular.copy(ctrl.availableTableConfig);
    ctrl.allocatedTableConfig.noItemsMessage = gettext(
      'Select an item from Available items below');

    ctrl.tableLimits = {
      maxAllocation: 1
    };

    var bootSources = {
      image: {
        available: $scope.model.images,
        allocated: selection,
        displayedAvailable: $scope.model.images,
        displayedAllocated: selection
      },
      snapshot: {
        available: $scope.model.imageSnapshots,
        allocated: selection,
        displayedAvailable: $scope.model.imageSnapshots,
        displayedAllocated: selection
      },
      volume: {
        available: $scope.model.volumes,
        allocated: selection,
        displayedAvailable: $scope.model.volumes,
        displayedAllocated: selection
      },
      volume_snapshot: {
        available: $scope.model.volumeSnapshots,
        allocated: selection,
        displayedAvailable: $scope.model.volumeSnapshots,
        displayedAllocated: selection
      }
    };

    var diskFormats = [
      { label: gettext('AKI'), key: 'aki' },
      { label: gettext('AMI'), key: 'ami' },
      { label: gettext('ARI'), key: 'ari' },
      { label: gettext('Docker'), key: 'docker' },
      { label: gettext('ISO'), key: 'iso' },
      { label: gettext('OVA'), key: 'ova' },
      { label: gettext('QCOW2'), key: 'qcow2' },
      { label: gettext('RAW'), key: 'raw' },
      { label: gettext('VDI'), key: 'vdi' },
      { label: gettext('VHD'), key: 'vhd' },
      { label: gettext('VMDK'), key: 'vmdk' }
    ];

    var diskFormatsObj = diskFormats.reduce(function (acc, cur) {
      acc[cur.key] = cur.label;
      return acc;
    }, {});

    function getImageDiskFormat(key) {
      return diskFormatsObj[key];
    }

    function getVolumeDiskFormat(data) {
      return diskFormatsObj[data.disk_format];
    }

    var statuses = [
          { label: gettext('Available'), key: 'available' },
          { label: gettext('Creating'), key: 'creating' },
          { label: gettext('Deleting'), key: 'deleting' },
          { label: gettext('Error'), key: 'error' },
          { label: gettext('Error Deleting'), key: 'error_deleting' }
    ];

    var statusesObj = statuses.reduce(function (acc, cur) {
      acc[cur.key] = cur.label;
      return acc;
    }, {});

    function getStatus(status) {
      return statusesObj[status];
    }

    // Mapping for dynamic table columns
    var tableColumnsMap = {
      image: [
        { id: 'name_or_id', title: gettext('Name'), priority: 1 },
        { id: 'updated_at', title: gettext('Updated'), filters: ['simpleDate'], priority: 2 },
        { id: 'size', title: gettext('Size'), filters: ['bytes'], priority: 2 },
        { id: 'disk_format', title: gettext('Type'), filters: [getImageDiskFormat], priority: 2 },
        { id: 'visibility', title: gettext('Visibility'), filters: [getVisibility], priority: 2 }
      ],
      snapshot: [
        { id: 'name', title: gettext('Name'), priority: 1 },
        { id: 'updated_at', title: gettext('Updated'), filters: ['simpleDate'], priority: 2 },
        { id: 'size', title: gettext('Size'), filters: ['bytes'], priority: 2 },
        { id: 'disk_format', title: gettext('Type'), filters: [getImageDiskFormat], priority: 2 },
        { id: 'visibility', title: gettext('Visibility'), filters: [getVisibility], priority: 2 }
      ],
      volume: [
        { id: 'name', title: gettext('Name'), priority: 1 },
        { id: 'description', title: gettext('Description'), filters: ['noValue'], priority: 2 },
        { id: 'size', title: gettext('Size'), filters: ['gb'], priority: 2 },
        { id: 'volume_image_metadata', title: gettext('Type'),
          filters: [getVolumeDiskFormat], priority: 2 },
        { id: 'availability_zone', title: gettext('Availability Zone'), priority: 2 }
      ],
      volume_snapshot: [
        { id: 'name', title: gettext('Name'), priority: 1 },
        { id: 'description', title: gettext('Description'), filters: ['noValue'], priority: 2 },
        { id: 'size', title: gettext('Size'), filters: ['gb'], priority: 2 },
        { id: 'created_at', title: gettext('Created'), filters: ['simpleDate'], priority: 2 },
        { id: 'status', title: gettext('Status'), filters: [getStatus], priority: 2 }
      ]
    };

    // Map Visibility data so we can decode true/false to Public/Private
    var _visibilitymap = { 'public': gettext('Public'),
                           'private': gettext('Private'),
                           'shared': gettext('Shared'),
                           'community': gettext('Community')
    };

    function getVisibility(visibility) {
      return _visibilitymap[visibility];
    }

    /**
     * Creates a map of functions that sort by the key at a given index for
     * the selected object
     */
    ctrl.sortByField = [];

    var sortFunction = function(columnIndex, comparedObject) {
      var cell = tableColumnsMap[ctrl.currentBootSource];
      var key = cell[columnIndex].id;
      return comparedObject[key];
    };

    for (var i = 0; i < 5; ++i) {
      ctrl.sortByField.push(sortFunction.bind(null, i));
    }

    /**
     * Filtering - client-side MagicSearch
     */
    ctrl.sourceFacets = [];

    // All facets for source step
    var facets = {
      created: {
        label: gettext('Created'),
        name: 'created_at',
        singleton: true
      },
      description: {
        label: gettext('Description'),
        name: 'description',
        singleton: true
      },
      encrypted: {
        label: gettext('Encrypted'),
        name: 'encrypted',
        singleton: true,
        options: [
          { label: gettext('Yes'), key: 'true' },
          { label: gettext('No'), key: 'false' }
        ]
      },
      name: {
        label: gettext('Name'),
        name: 'name',
        singleton: true
      },
      size: {
        label: gettext('Size'),
        name: 'size',
        singleton: true
      },
      status: {
        label: gettext('Status'),
        name: 'status',
        singleton: true,
        options: statuses
      },
      type: {
        label: gettext('Type'),
        name: 'disk_format',
        singleton: true,
        options: diskFormats
      },
      updated: {
        label: gettext('Updated'),
        name: 'updated_at',
        singleton: true
      },
      visibility: {
        label: gettext('Visibility'),
        name: 'visibility',
        singleton: true,
        options: [
          { label: gettext('Public'), key: 'public' },
          { label: gettext('Private'), key: 'private' },
          { label: gettext('Shared With Project'), key: 'shared' },
          { label: gettext('Community'), key: 'community' }
        ]
      },
      volumeType: {
        label: gettext('Type'),
        name: 'volume_image_metadata.disk_format',
        singleton: true,
        options: diskFormats
      }
    };

    // Mapping for filter facets based on boot source type
    var sourceTypeFacets = {
      image: [
        facets.name, facets.updated, facets.size, facets.type, facets.visibility
      ],
      snapshot: [
        facets.name, facets.updated, facets.size, facets.type, facets.visibility
      ],
      volume: [
        facets.name, facets.description, facets.size, facets.volumeType, facets.encrypted
      ],
      volume_snapshot: [
        facets.name, facets.description, facets.size, facets.created, facets.status
      ]
    };

    var newSpecWatcher = $scope.$watch(
      function () {
        return $scope.model.newInstanceSpec.instance_count;
      },
      function (newValue, oldValue) {
        if (newValue !== oldValue) {
          validateBootSourceType();
        }
      }
    );

    var allocatedWatcher = $scope.$watch(
      function () {
        return ctrl.tableData.allocated.length;
      },
      function (newValue) {
        checkVolumeForImage(newValue);
      }
    );

    // Since available transfer table for Launch Instance Source step is
    // dynamically selected based on Boot Source, we need to update the
    // model here accordingly. Otherwise it will only calculate the items
    // available based on the original selection Boot Source: Image.
    var bootSourceWatcher = $scope.$watch(
      function getBootSource() {
        return ctrl.currentBootSource;
      },
      function onBootSourceChange(newValue, oldValue) {
        if (newValue !== oldValue) {
          $scope.$broadcast(events.TABLES_CHANGED, {
            'data': bootSources[newValue]
          });
        }
      }
    );

    var imagesWatcher = $scope.$watchCollection(
      function getImages() {
        return $scope.model.images;
      },
      function onImagesChange() {
        $scope.initPromise.then(function () {
          $scope.$applyAsync(function () {
            if ($scope.launchContext.imageId) {
              setSourceImageWithId($scope.launchContext.imageId);
            }
          });
        });
      }
    );

    var imageSnapshotsWatcher = $scope.$watchCollection(
      function getImageSnapshots() {
        return $scope.model.imageSnapshots;
      },
      function onImageSnapshotsChange() {
        $scope.initPromise.then(function () {
          $scope.$applyAsync(function () {
            if ($scope.launchContext.imageId) {
              setSourceImageSnapshotWithId($scope.launchContext.imageId);
            }
          });
        });
      }
    );

    var volumeWatcher = $scope.$watchCollection(
      function getVolumes() {
        return $scope.model.volumes;
      },
      function onVolumesChange() {
        $scope.initPromise.then(function onInit() {
          $scope.$applyAsync(function setDefaultVolume() {
            if ($scope.launchContext.volumeId) {
              setSourceVolumeWithId($scope.launchContext.volumeId);
            }
          });
        });
      }
    );

    var snapshotWatcher = $scope.$watchCollection(
      function getSnapshots() {
        return $scope.model.volumeSnapshots;
      },
      function onSnapshotsChange() {
        $scope.initPromise.then(function onInit() {
          $scope.$applyAsync(function setDefaultSnapshot() {
            if ($scope.launchContext.snapshotId) {
              setSourceSnapshotWithId($scope.launchContext.snapshotId);
            }
          });
        });
      }
    );

    // When the allowedboot list changes, change the source_type
    // and update the table for the new source selection. The devault value is
    // set by the DEFAULT_BOOT_SOURCE config option.
    // The boot source is changed only if the selected value is not included
    // in the updated list (newValue)
    var allowedBootSourcesWatcher = $scope.$watchCollection(
      function getAllowedBootSources() {
        return $scope.model.allowedBootSources;
      },
      function changeBootSource(newValue) {
        if (angular.isArray(newValue) && newValue.length > 0 ) {
          var opt = newValue[0];
          for (var index = 0; index < newValue.length; index++) {
            if (newValue[index].selected) {
              opt = newValue[index];
            }
          }
          updateBootSourceSelection(opt.type);
          $scope.model.newInstanceSpec.source_type = opt;
        }
      }
    );

    var flavorWatcher = $scope.$watchCollection(function () {
      return $scope.model.newInstanceSpec.flavor;
    }, function setVolumeSize() {
      // Set the volume size if a flavor is selected and it requires
      // more disk space than what the user specified.
      var newInstanceSpec = $scope.model.newInstanceSpec;
      var flavor = newInstanceSpec.flavor;
      if (flavor && (newInstanceSpec.vol_size < flavor.disk)) {
        newInstanceSpec.vol_size = flavor.disk;
      }
    });

    // Explicitly remove watchers on destruction of this controller
    $scope.$on('$destroy', function() {
      allowedBootSourcesWatcher();
      newSpecWatcher();
      allocatedWatcher();
      bootSourceWatcher();
      imagesWatcher();
      imageSnapshotsWatcher();
      volumeWatcher();
      snapshotWatcher();
      flavorWatcher();
    });

    ////////////////////

    function updateBootSourceSelection(selectedSource, preSelection) {
      if (ctrl.currentBootSource !== selectedSource) {
        ctrl.selection.length = 0;
        ctrl.currentBootSource = selectedSource;
      }
      if ((selectedSource === bootSourceTypes.IMAGE ||
           selectedSource === bootSourceTypes.INSTANCE_SNAPSHOT) && $scope.model.volumeBootable) {
        $scope.model.newInstanceSpec.vol_create =
          $scope.model.newInstanceSpec.create_volume_default;
      } else {
        $scope.model.newInstanceSpec.vol_create = false;
      }
      $scope.model.newInstanceSpec.vol_delete_on_instance_delete = false;
      changeBootSource(selectedSource, preSelection);
      validateBootSourceType();
    }

    // Dynamically update page based on boot source selection
    function changeBootSource(key, preSelection) {
      updateDataSource(key, preSelection);
      updateHelpText(key);
      updateTableColumns(key);
      updateFacets(key);
    }

    function updateDataSource(key, preSelection) {
      if (preSelection) {
        ctrl.selection.length = 0;
        push.apply(selection, preSelection);
      }
      angular.extend(ctrl.tableData, bootSources[key]);
    }

    function updateHelpText() {
      angular.extend(ctrl.helpText, {
        noneAllocText: gettext('Select a source from those listed below.'),
        availHelpText: gettext('Select one'),
        /*eslint-disable max-len */
        volumeAZHelpText: gettext('When selecting volume as boot source, please ensure the instance\'s availability zone is compatible with your volume\'s availability zone.')
        /*eslint-enable max-len */
      });
    }

    function updateTableColumns(key) {
      refillArray(ctrl.availableTableConfig.columns, tableColumnsMap[key]);
      refillArray(ctrl.allocatedTableConfig.columns, tableColumnsMap[key]);
    }

    function updateFacets(key) {
      refillArray(ctrl.sourceFacets, sourceTypeFacets[key]);
      $scope.$broadcast(magicSearchEvents.FACETS_CHANGED);
    }

    function refillArray(arrayToRefill, contentArray) {
      arrayToRefill.length = 0;
      Array.prototype.push.apply(arrayToRefill, contentArray);
    }

    /*
     * Validation
     */

    /*
     * If boot source type is 'image' and 'Create New Volume' is checked, set the minimum volume
     * size for validating vol_size field
     */
    function checkVolumeForImage() {
      var source = selection[0];

      if (source && ctrl.currentBootSource === bootSourceTypes.IMAGE ||
          source && ctrl.currentBootSource === bootSourceTypes.INSTANCE_SNAPSHOT ) {
        var imageGb = source.size / 1073741824.0;
        var imageDisk = source.min_disk;
        ctrl.minVolumeSize = Math.ceil(Math.max(imageGb, imageDisk));
        if ($scope.model.newInstanceSpec.vol_size < ctrl.minVolumeSize) {
          $scope.model.newInstanceSpec.vol_size = ctrl.minVolumeSize;
        }
        var volumeSizeText = gettext('The volume size must be at least %(minVolumeSize)s GB');
        var volumeSizeObj = { minVolumeSize: ctrl.minVolumeSize };
        ctrl.minVolumeSizeError = interpolate(volumeSizeText, volumeSizeObj, true);
      } else {
        ctrl.minVolumeSize = 0;
        ctrl.minVolumeSizeError = gettext('Volume size is required and must be an integer');
      }
    }

    // Validator for boot source type. Instance count must to be 1 if volume selected
    function validateBootSourceType() {
      var bootSourceType = ctrl.currentBootSource;
      var instanceCount = $scope.model.newInstanceSpec.instance_count;

      /*
       * Field is valid if boot source type is not volume, instance count is blank/undefined
       * (this is an error with instance count) or instance count is 1
       */
      var isValid = bootSourceType !== bootSourceTypes.VOLUME ||
                    !instanceCount ||
                    instanceCount === 1;

      $scope.launchInstanceSourceForm['boot-source-type']
            .$setValidity('bootSourceType', isValid);
    }

    function findSourceById(sources, id) {
      var len = sources.length;
      var source;
      for (var i = 0; i < len; i++) {
        source = sources[i];
        if (source.id === id) {
          return source;
        }
      }
    }

    function setSourceImageWithId(id) {
      var pre = findSourceById($scope.model.images, id);
      if (pre) {
        updateBootSourceSelection(bootSourceTypes.IMAGE, [pre]);
        $scope.model.newInstanceSpec.source_type = {
          type: bootSourceTypes.IMAGE,
          label: gettext('Image')
        };
      }
    }

    function setSourceImageSnapshotWithId(id) {
      var pre = findSourceById($scope.model.imageSnapshots, id);
      if (pre) {
        updateBootSourceSelection(bootSourceTypes.INSTANCE_SNAPSHOT, [pre]);
        $scope.model.newInstanceSpec.source_type = {
          type: bootSourceTypes.INSTANCE_SNAPSHOT,
          label: gettext('Snapshot')
        };
      }
    }

    function setSourceVolumeWithId(id) {
      var pre = findSourceById($scope.model.volumes, id);
      if (pre) {
        updateBootSourceSelection(bootSourceTypes.VOLUME, [pre]);
        $scope.model.newInstanceSpec.source_type = {
          type: bootSourceTypes.VOLUME,
          label: gettext('Volume')
        };
      }
    }

    function setSourceSnapshotWithId(id) {
      var pre = findSourceById($scope.model.volumeSnapshots, id);
      if (pre) {
        updateBootSourceSelection(bootSourceTypes.VOLUME_SNAPSHOT, [pre]);
        $scope.model.newInstanceSpec.source_type = {
          type: bootSourceTypes.VOLUME_SNAPSHOT,
          label: gettext('Snapshot')
        };
      }
    }
  }
})();
