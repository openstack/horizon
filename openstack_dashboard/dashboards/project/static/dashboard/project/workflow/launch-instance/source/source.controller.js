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
    'horizon.framework.widgets.transfer-table.events'
  ];

  function LaunchInstanceSourceController($scope,
    bootSourceTypes,
    bytesFilter,
    dateFilter,
    decodeFilter,
    diskFormatFilter,
    gbFilter,
    basePath,
    events
  ) {

    var ctrl = this;

    // Error text for invalid fields
    /*eslint-disable max-len */
    ctrl.bootSourceTypeError = gettext('Volumes can only be attached to 1 active instance at a time. Please either set your instance count to 1 or select a different source type.');
    /*eslint-enable max-len */
    ctrl.volumeSizeError = gettext('Volume size is required and must be an integer');

    // toggle button label/value defaults
    ctrl.toggleButtonOptions = [
      { label: gettext('Yes'), value: true },
      { label: gettext('No'), value: false }
    ];

    /*
     * Boot Sources
     */
    ctrl.bootSourcesOptions = [
      { type: bootSourceTypes.IMAGE, label: gettext('Image') },
      { type: bootSourceTypes.INSTANCE_SNAPSHOT, label: gettext('Instance Snapshot') },
      { type: bootSourceTypes.VOLUME, label: gettext('Volume') },
      { type: bootSourceTypes.VOLUME_SNAPSHOT, label: gettext('Volume Snapshot') }
    ];

    ctrl.updateBootSourceSelection = updateBootSourceSelection;

    /*
     * Transfer table
     */
    ctrl.tableHeadCells = [];
    ctrl.tableBodyCells = [];
    ctrl.tableData = {};
    ctrl.helpText = {};
    ctrl.sourceDetails = basePath + 'source/source-details.html';

    var selection = ctrl.selection = $scope.model.newInstanceSpec.source;

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
        { text: gettext('Name'), style: { width: '30%' }, sortable: true, sortDefault: true },
        { text: gettext('Updated'), style: { width: '15%' }, sortable: true },
        { text: gettext('Size'), style: { width: '15%' }, classList: ['number'], sortable: true },
        { text: gettext('Type'), sortable: true },
        { text: gettext('Visibility'), sortable: true }
      ],
      snapshot: [
        { text: gettext('Name'), style: { width: '30%' }, sortable: true, sortDefault: true },
        { text: gettext('Updated'), style: { width: '15%' }, sortable: true },
        { text: gettext('Size'), style: { width: '15%' }, classList: ['number'], sortable: true },
        { text: gettext('Type'), sortable: true },
        { text: gettext('Visibility'), sortable: true }
      ],
      volume: [
        { text: gettext('Name'), style: { width: '25%' }, sortable: true, sortDefault: true },
        { text: gettext('Description'), style: { width: '20%' }, sortable: true },
        { text: gettext('Size'), style: { width: '15%' }, classList: ['number'], sortable: true },
        { text: gettext('Type'), style: { width: '20%' }, sortable: true },
        { text: gettext('Availability Zone'), style: { width: '20%' }, sortable: true }
      ],
      volume_snapshot: [
        { text: gettext('Name'), style: { width: '25%' }, sortable: true, sortDefault: true },
        { text: gettext('Description'), style: { width: '20%' }, sortable: true },
        { text: gettext('Size'), style: { width: '15%' }, classList: ['number'], sortable: true },
        { text: gettext('Created'), style: { width: '15%' }, sortable: true },
        { text: gettext('Status'), style: { width: '20%' }, sortable: true }
      ]
    };

    // Map Visibility data so we can decode true/false to Public/Private
    var _visibilitymap = { true: gettext('Public'), false: gettext('Private') };

    // Mapping for dynamic table data
    var tableBodyCellsMap = {
      image: [
        { key: 'name', classList: ['hi-light'] },
        { key: 'updated_at', filter: dateFilter, filterArg: 'short' },
        { key: 'size', filter: bytesFilter, classList: ['number'] },
        { key: 'disk_format', style: { 'text-transform': 'uppercase' },
          filter: diskFormatFilter, filterRawData: true },
        { key: 'is_public', filter: decodeFilter, filterArg: _visibilitymap,
          style: { 'text-transform': 'capitalize' } }
      ],
      snapshot: [
        { key: 'name', classList: ['hi-light'] },
        { key: 'updated_at', filter: dateFilter, filterArg: 'short' },
        { key: 'size', filter: bytesFilter, classList: ['number'] },
        { key: 'disk_format', style: { 'text-transform': 'uppercase' },
          filter: diskFormatFilter, filterRawData: true },
        { key: 'is_public', filter: decodeFilter, filterArg: _visibilitymap,
          style: { 'text-transform': 'capitalize' } }
      ],
      volume: [
        { key: 'name', classList: ['hi-light'] },
        { key: 'description' },
        { key: 'size', filter: gbFilter, classList: ['number'] },
        { key: 'volume_image_metadata', filter: diskFormatFilter,
          style: { 'text-transform': 'uppercase' } },
        { key: 'availability_zone' }
      ],
      volume_snapshot: [
        { key: 'name', classList: ['hi-light'] },
        { key: 'description' },
        { key: 'size', filter: gbFilter, classList: ['number'] },
        { key: 'created_at', filter: dateFilter, filterArg: 'short' },
        { key: 'status', style: { 'text-transform': 'capitalize' } }
      ]
    };

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
        name: 'is_public',
        singleton: true,
        options: [
          { label: gettext('Public'), key: 'true' },
          { label: gettext('Private'), key: 'false' }
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
          $scope.$broadcast(events.AVAIL_CHANGED, {
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

    // Explicitly remove watchers on desruction of this controller
    $scope.$on('$destroy', function() {
      newSpecWatcher();
      allocatedWatcher();
      bootSourceWatcher();
      imagesWatcher();
      volumeWatcher();
    });

    // Initialize
    changeBootSource(ctrl.bootSourcesOptions[0].type);

    if (!$scope.model.newInstanceSpec.source_type) {
      $scope.model.newInstanceSpec.source_type = ctrl.bootSourcesOptions[0];
      ctrl.currentBootSource = ctrl.bootSourcesOptions[0].type;
    }

    ////////////////////

    function updateBootSourceSelection(selectedSource) {
      ctrl.currentBootSource = selectedSource;
      $scope.model.newInstanceSpec.vol_create = false;
      $scope.model.newInstanceSpec.vol_delete_on_instance_delete = false;
      changeBootSource(selectedSource);
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
      selection.length = 0;
      if (preSelection) {
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
      $scope.$broadcast('facetsChanged');
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

      if (source && ctrl.currentBootSource === bootSourceTypes.IMAGE) {
        var imageGb = source.size * 1e-9;
        var imageDisk = source.min_disk;
        ctrl.minVolumeSize = Math.ceil(Math.max(imageGb, imageDisk));

        var volumeSizeText = gettext('The volume size must be at least %(minVolumeSize)s GB');
        var volumeSizeObj = { minVolumeSize: ctrl.minVolumeSize };
        ctrl.minVolumeSizeError = interpolate(volumeSizeText, volumeSizeObj, true);
      } else {
        /*eslint-disable no-undefined */
        ctrl.minVolumeSize = undefined;
        /*eslint-enable no-undefined */
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
        changeBootSource(bootSourceTypes.IMAGE, [pre]);
        $scope.model.newInstanceSpec.source_type = ctrl.bootSourcesOptions[0];
        ctrl.currentBootSource = ctrl.bootSourcesOptions[0].type;
      }
    }

    function setSourceVolumeWithId(id) {
      var pre = findSourceById($scope.model.volumes, id);
      if (pre) {
        changeBootSource(bootSourceTypes.VOLUME, [pre]);
        $scope.model.newInstanceSpec.source_type = ctrl.bootSourcesOptions[2];
        ctrl.currentBootSource = ctrl.bootSourcesOptions[2].type;
      }
    }
  }
})();
