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
    'bytesFilter',
    'dateFilter',
    'decodeFilter',
    'diskFormatFilter',
    'gbFilter',
    'horizon.dashboard.project.workflow.launch-instance.basePath',
    'horizon.framework.widgets.transfer-table.events',
    'horizon.framework.widgets.magic-search.events'
  ];

  function LaunchInstanceSourceController($scope,
    bootSourceTypes,
    bytesFilter,
    dateFilter,
    decodeFilter,
    diskFormatFilter,
    gbFilter,
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
    ctrl.tableHeadCells = [];
    ctrl.tableBodyCells = [];
    ctrl.tableData = {
      available: [],
      allocated: selection,
      displayedAvailable: [],
      displayedAllocated: []
    };
    ctrl.helpText = {};
    ctrl.sourceDetails = basePath + 'source/source-details.html';

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
        displayedAvailable: [],
        displayedAllocated: selection
      },
      volume: {
        available: $scope.model.volumes,
        allocated: selection,
        displayedAvailable: [],
        displayedAllocated: selection
      },
      volume_snapshot: {
        available: $scope.model.volumeSnapshots,
        allocated: selection,
        displayedAvailable: [],
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

    // Mapping for dynamic table headers
    var tableHeadCellsMap = {
      image: [
        { text: gettext('Name') },
        { text: gettext('Updated') },
        { text: gettext('Size') },
        { text: gettext('Type') },
        { text: gettext('Visibility') }
      ],
      snapshot: [
        { text: gettext('Name') },
        { text: gettext('Updated') },
        { text: gettext('Size') },
        { text: gettext('Type') },
        { text: gettext('Visibility') }
      ],
      volume: [
        { text: gettext('Name') },
        { text: gettext('Description') },
        { text: gettext('Size') },
        { text: gettext('Type') },
        { text: gettext('Availability Zone') }
      ],
      volume_snapshot: [
        { text: gettext('Name') },
        { text: gettext('Description') },
        { text: gettext('Size') },
        { text: gettext('Created') },
        { text: gettext('Status') }
      ]
    };

    // Map Visibility data so we can decode true/false to Public/Private
    var _visibilitymap = { 'public': gettext('Public'),
                           'private': gettext('Private'),
                           'shared': gettext('Shared'),
                           'community': gettext('Community')
    };

    // Mapping for dynamic table data
    var tableBodyCellsMap = {
      image: [
        { key: 'name', classList: ['hi-light', 'word-break'] },
        { key: 'updated_at', filter: dateFilter, filterArg: 'short' },
        { key: 'size', filter: bytesFilter, classList: ['number'] },
        { key: 'disk_format', filter: diskFormatFilter, filterRawData: true },
        { key: 'visibility', filter: decodeFilter, filterArg: _visibilitymap }
      ],
      snapshot: [
        { key: 'name', classList: ['hi-light', 'word-break'] },
        { key: 'updated_at', filter: dateFilter, filterArg: 'short' },
        { key: 'size', filter: bytesFilter, classList: ['number'] },
        { key: 'disk_format', filter: diskFormatFilter, filterRawData: true },
        { key: 'visibility', filter: decodeFilter, filterArg: _visibilitymap }
      ],
      volume: [
        { key: 'name', classList: ['hi-light', 'word-break'] },
        { key: 'description' },
        { key: 'size', filter: gbFilter, classList: ['number'] },
        { key: 'volume_image_metadata', filter: diskFormatFilter },
        { key: 'availability_zone' }
      ],
      volume_snapshot: [
        { key: 'name', classList: ['hi-light', 'word-break'] },
        { key: 'description' },
        { key: 'size', filter: gbFilter, classList: ['number'] },
        { key: 'created_at', filter: dateFilter, filterArg: 'short' },
        { key: 'status' }
      ]
    };

    /**
     * Creates a map of functions that sort by the key at a given index for
     * the selected object
     */
    ctrl.sortByField = [];

    var sortFunction = function(columnIndex, comparedObject) {
      var cell = tableBodyCellsMap[ctrl.currentBootSource];
      var key = cell[columnIndex].key;
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
        options: [
          { label: gettext('Available'), key: 'available' },
          { label: gettext('Creating'), key: 'creating' },
          { label: gettext('Deleting'), key: 'deleting' },
          { label: gettext('Error'), key: 'error' },
          { label: gettext('Error Deleting'), key: 'error_deleting' }
        ]
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
    // and update the table for the new source selection. Only done
    // with the first item for the list
    // The boot source is changed only if the selected value is not included
    // in the updated list (newValue)
    var allowedBootSourcesWatcher = $scope.$watchCollection(
      function getAllowedBootSources() {
        return $scope.model.allowedBootSources;
      },
      function changeBootSource(newValue) {
        if (angular.isArray(newValue) && newValue.length > 0 ) {
          if (!$scope.model.newInstanceSpec.source_type ||
              newValue.filter(function(value) {
                return value.type === $scope.model.newInstanceSpec.source_type.type;
              }).length === 0) {
            updateBootSourceSelection(newValue[0].type);
            $scope.model.newInstanceSpec.source_type = newValue[0];
          }
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
      updateTableHeadCells(key);
      updateTableBodyCells(key);
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

    function updateTableHeadCells(key) {
      refillArray(ctrl.tableHeadCells, tableHeadCellsMap[key]);
    }

    function updateTableBodyCells(key) {
      refillArray(ctrl.tableBodyCells, tableBodyCellsMap[key]);
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
