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
    'horizon.framework.widgets.charts.donutChartSettings',
    'dateFilter',
    'decodeFilter',
    'diskFormatFilter',
    'gbFilter',
    'horizon.framework.widgets.charts.quotaChartDefaults',
    'horizon.dashboard.project.workflow.launch-instance.basePath'
  ];

  function LaunchInstanceSourceController($scope,
    bootSourceTypes,
    bytesFilter,
    donutChartSettings,
    dateFilter,
    decodeFilter,
    diskFormatFilter,
    gbFilter,
    quotaChartDefaults,
    basePath
  ) {

    var ctrl = this;

    ctrl.label = {
      title: gettext('Instance Details'),
      /*eslint-disable max-len */
      subtitle: gettext('Please provide the initial host name for the instance, the availability zone where it will be deployed, and the instance count. Increase the Count to create multiple instances with the same settings.'),
      /*eslint-enable max-len */
      instanceName: gettext('Instance Name'),
      availabilityZone: gettext('Availability Zone'),
      instance_count: gettext('Count'),
      instanceSourceTitle: gettext('Instance Source'),
      /*eslint-disable max-len */
      instanceSourceSubTitle: gettext('Instance source is the template used to create an instance. You can use a snapshot of an existing instance, an image, or a volume (if enabled). You can also choose to use persistent storage by creating a new volume.'),
      /*eslint-enable max-len */
      bootSource: gettext('Select Boot Source'),
      volumeSize: gettext('Size (GB)'),
      volumeCreate: gettext('Create New Volume'),
      volumeDeviceName: gettext('Device Name'),
      deleteVolumeOnTerminate: gettext('Delete Volume on Terminate'),
      id: gettext('ID'),
      min_ram: gettext('Min Ram'),
      min_disk: gettext('Min Disk')
    };

    // Error text for invalid fields
    /*eslint-disable max-len */
    ctrl.bootSourceTypeError = gettext('Volumes can only be attached to 1 active instance at a time. Please either set your instance count to 1 or select a different source type.');
    /*eslint-enable max-len */
    ctrl.instanceNameError = gettext('A name is required for your instance.');
    ctrl.instanceCountError = gettext(
      'Instance count is required and must be an integer of at least 1'
    );
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
    ctrl.maxInstanceCount = 1;
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
        { key: 'disk_format', style: { 'text-transform': 'uppercase' } },
        { key: 'is_public', filter: decodeFilter, filterArg: _visibilitymap,
          style: { 'text-transform': 'capitalize' } }
      ],
      snapshot: [
        { key: 'name', classList: ['hi-light'] },
        { key: 'updated_at', filter: dateFilter, filterArg: 'short' },
        { key: 'size', filter: bytesFilter, classList: ['number'] },
        { key: 'disk_format', style: { 'text-transform': 'uppercase' } },
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

    /*
     * Donut chart
     */
    ctrl.chartSettings = donutChartSettings;
    var maxTotalInstances = 1; // Must have default value > 0
    var totalInstancesUsed = 0;

    if ($scope.model.novaLimits && $scope.model.novaLimits.maxTotalInstances) {
      maxTotalInstances = $scope.model.novaLimits.maxTotalInstances;
    }

    if ($scope.model.novaLimits && $scope.model.novaLimits.totalInstancesUsed) {
      totalInstancesUsed = $scope.model.novaLimits.totalInstancesUsed;
    }

    ctrl.instanceStats = {
      title: gettext('Total Instances'),
      maxLimit: maxTotalInstances,
      label: '100%',
      data: [
        {
          label: quotaChartDefaults.usageLabel,
          value: 1,
          colorClass: quotaChartDefaults.usageColorClass
        },
        {
          label: quotaChartDefaults.addedLabel,
          value: 1,
          colorClass: quotaChartDefaults.addedColorClass
        },
        {
          label: quotaChartDefaults.remainingLabel,
          value: 1,
          colorClass: quotaChartDefaults.remainingColorClass
        }
      ]
    };

    var newSpecWatcher = $scope.$watch(
      function () {
        return $scope.model.newInstanceSpec.instance_count;
      },
      function (newValue, oldValue) {
        if (newValue !== oldValue) {
          updateChart();
          validateBootSourceType();
        }
      }
    );

    var maxInstancesWatcher = $scope.$watch(
      function () {
        return $scope.model.novaLimits.maxTotalInstances;
      },
      function (newValue, oldValue) {
        if (newValue !== oldValue) {
          maxTotalInstances = Math.max(1, newValue);
          updateChart();
          updateMaxInstanceCount();
        }
      }
    );

    var instancesUsedWatcher = $scope.$watch(
      function () {
        return $scope.model.novaLimits.totalInstancesUsed;
      },
      function (newValue, oldValue) {
        if (newValue !== oldValue) {
          totalInstancesUsed = newValue;
          updateChart();
          updateMaxInstanceCount();
        }
      }
    );

    var allocatedWatcher = $scope.$watch(
      function () {
        return ctrl.tableData.allocated.length;
      },
      function (newValue, oldValue) {
        if (newValue !== oldValue) {
          updateChart();
        }
        checkVolumeForImage(newValue);
      }
    );

    var imagesWatcher = $scope.$watchCollection(
      function () {
        return $scope.model.images;
      },
      function () {
        $scope.initPromise.then(function () {
          $scope.$applyAsync(function () {
            if ($scope.launchContext.imageId) {
              setSourceImageWithId($scope.launchContext.imageId);
            }
          });
        });
      }
    );

    // Explicitly remove watchers on desruction of this controller
    $scope.$on('$destroy', function() {
      newSpecWatcher();
      maxInstancesWatcher();
      instancesUsedWatcher();
      allocatedWatcher();
      imagesWatcher();
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
      $scope.model.newInstanceSpec.vol_delete_on_terminate = false;
      changeBootSource(selectedSource);
      validateBootSourceType();
    }

    // Dynamically update page based on boot source selection
    function changeBootSource(key, preSelection) {
      updateDataSource(key, preSelection);
      updateHelpText(key);
      updateTableHeadCells(key);
      updateTableBodyCells(key);
      updateChart();
      updateMaxInstanceCount();
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
      refillArray(ctrl.tableHeadCells,  tableHeadCellsMap[key]);
    }

    function updateTableBodyCells(key) {
      refillArray(ctrl.tableBodyCells, tableBodyCellsMap[key]);
    }

    function refillArray(arrayToRefill, contentArray) {
      arrayToRefill.length = 0;
      Array.prototype.push.apply(arrayToRefill, contentArray);
    }

    function updateChart() {
      // Initialize instance_count to 1
      if ($scope.model.newInstanceSpec.instance_count <= 0) {
        $scope.model.newInstanceSpec.instance_count = 1;
      }

      var data = ctrl.instanceStats.data;
      var added = $scope.model.newInstanceSpec.instance_count || 1;
      var remaining = Math.max(0, maxTotalInstances - totalInstancesUsed - added);

      ctrl.instanceStats.maxLimit = maxTotalInstances;
      data[0].value = totalInstancesUsed;
      data[1].value = added;
      data[2].value = remaining;
      var quotaCalc = Math.round((totalInstancesUsed + added) / maxTotalInstances * 100);
      ctrl.instanceStats.overMax = quotaCalc > 100 ? true : false;
      ctrl.instanceStats.label = quotaCalc + '%';
      ctrl.instanceStats = angular.extend({}, ctrl.instanceStats);
    }

    /*
     * Validation
     */

    /*
     * If boot source type is 'image' and 'Create New Volume' is checked, set the minimum volume
     * size for validating vol_size field
     */
    function checkVolumeForImage() {
      var source = selection ? selection[0] : undefined;

      if (source && ctrl.currentBootSource === bootSourceTypes.IMAGE) {
        var imageGb = source.size * 1e-9;
        var imageDisk = source.min_disk;
        ctrl.minVolumeSize = Math.ceil(Math.max(imageGb, imageDisk));

        var volumeSizeText = gettext('The volume size must be at least %(minVolumeSize)s GB');
        var volumeSizeObj = { minVolumeSize: ctrl.minVolumeSize };
        ctrl.minVolumeSizeError = interpolate(volumeSizeText, volumeSizeObj, true);
      } else {
        ctrl.minVolumeSize = undefined;
      }
    }

    // Update the maximum instance count based on nova limits
    function updateMaxInstanceCount() {
      ctrl.maxInstanceCount = maxTotalInstances - totalInstancesUsed;

      var instanceCountText = gettext(
        'The instance count must not exceed your quota available of %(maxInstanceCount)s instances'
      );
      var instanceCountObj = { maxInstanceCount: ctrl.maxInstanceCount };
      ctrl.instanceCountMaxError = interpolate(instanceCountText, instanceCountObj, true);
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
  }
})();
