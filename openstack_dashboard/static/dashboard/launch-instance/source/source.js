(function () {
  'use strict';

  var push = [].push,
      forEach = angular.forEach;

  /**
   * @ngdoc overview
   * @name hz.dashboard.launch-instance
   * @description
   *
   * # hz.dashboard.launch-instance
   *
   * The `hz.dashboard.launch-instance` module allows a user
   * to launch an instance via the multi-step wizard framework
   *
   */
  var module = angular.module('hz.dashboard.launch-instance');

  /**
   * @name bootSourceTypes
   * @description Boot source types
   */
  module.constant('bootSourceTypes', {
    IMAGE: 'image',
    INSTANCE_SNAPSHOT: 'snapshot',
    VOLUME: 'volume',
    VOLUME_SNAPSHOT: 'volume_snapshot'
  });

  /**
   * @ngdoc filter
   * @name diskFormat
   * @description
   * Expects object and returns disk_format property value.
   * Returns empty string if input is null or not an object.
   * Uniquely required for the source step implementation of transfer tables
   */
  module.filter('diskFormat', function() {
    return function(input) {
      if (input === null || !angular.isObject(input) ||
        !angular.isDefined(input.disk_format) || input.disk_format === null) {
        return '';
      } else {
        return input.disk_format.toUpperCase();
      }
    };
  });

  /**
   * @ngdoc controller
   * @name LaunchInstanceSourceCtrl
   * @description
   * The `LaunchInstanceSourceCtrl` controller provides functions for
   * configuring the source step of the Launch Instance Wizard.
   *
   */
  module.controller('LaunchInstanceSourceCtrl', [
    '$scope',
    'bootSourceTypes',
    'bytesFilter',
    'dateFilter',
    'decodeFilter',
    'diskFormatFilter',
    'gbFilter',
    '$window',
    LaunchInstanceSourceCtrl
  ]);

  function LaunchInstanceSourceCtrl($scope,
                                    bootSourceTypes,
                                    bytesFilter,
                                    dateFilter,
                                    decodeFilter,
                                    diskFormatFilter,
                                    gbFilter,
                                    $window) {

    $scope.label = {
      title: gettext('Instance Details'),
      subtitle: gettext('Please provide the initial host name for the instance, the availability zone where it will be deployed, and the instance count. Increase the Count to create multiple instances with the same settings.'),
      instanceName: gettext('Instance Name'),
      availabilityZone: gettext('Availability Zone'),
      instance_count: gettext('Count'),
      instanceSourceTitle: gettext('Instance Source'),
      instanceSourceSubTitle: gettext('Instance source is the template used to create an instance. You can use a snapshot of an existing instance, an image, or a volume (if enabled). You can also choose to use persistent storage by creating a new volume.'),
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
    $scope.bootSourceTypeError = gettext('Volumes can only be attached to 1 active instance at a time. Please either set your instance count to 1 or select a different source type.');
    $scope.instanceNameError = gettext('A name is required for your instance.');
    $scope.instanceCountError = gettext('Instance count is required and must be an integer of at least 1');
    $scope.volumeSizeError = gettext('Volume size is required and must be an integer');


    // toggle button label/value defaults
    $scope.toggleButtonOptions = [
      { label: gettext('Yes'), value: true },
      { label: gettext('No'), value: false }
    ];

    //
    // Boot Sources
    //

    $scope.bootSourcesOptions = [
      { type: bootSourceTypes.IMAGE, label: gettext('Image') },
      { type: bootSourceTypes.INSTANCE_SNAPSHOT, label: gettext('Instance Snapshot') },
      { type: bootSourceTypes.VOLUME, label: gettext('Volume') },
      { type: bootSourceTypes.VOLUME_SNAPSHOT, label: gettext('Volume Snapshot') }
    ];

    $scope.updateBootSourceSelection = function (selectedSource) {
      $scope.currentBootSource = selectedSource;
      $scope.model.newInstanceSpec.vol_create = false;
      $scope.model.newInstanceSpec.vol_delete_on_terminate = false;
      changeBootSource(selectedSource);
      validateBootSourceType();
    };

    //
    // Transfer table
    //

    $scope.tableHeadCells = [];
    $scope.tableBodyCells= [];
    $scope.tableData = {};
    $scope.helpText = {};
    $scope.maxInstanceCount = 1;
    $scope.sourceDetails = $window.STATIC_URL +
      'dashboard/launch-instance/source/source-details.html';

    var selection = $scope.selection = $scope.model.newInstanceSpec.source;

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

    // mapping for dynamic table headers
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

    // map Visibility data so we can decode true/false to Public/Private
    var _visibilitymap = { true: gettext('Public'), false: gettext('Private') };

    // mapping for dynamic table data
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

    // dynamically update page based on boot source selection
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
      angular.extend($scope.tableData, bootSources[key]);
    }

    function updateHelpText(key) {
      angular.extend($scope.helpText, {
        noneAllocText: gettext('Select a source from those listed below.'),
        availHelpText: gettext('Select one'),
        volumeAZHelpText: gettext("When selecting volume as boot source, please ensure the instance's availability zone is compatible with your volume's availability zone.")
      });
    }

    function updateTableHeadCells(key) {
      refillArray($scope.tableHeadCells,  tableHeadCellsMap[key]);
    }

    function updateTableBodyCells(key) {
      refillArray($scope.tableBodyCells, tableBodyCellsMap[key]);
    }

    function refillArray(arrayToRefill, contentArray) {
      arrayToRefill.length = 0;
      Array.prototype.push.apply(arrayToRefill, contentArray);
    }

    //
    // Donut chart
    //

    var maxTotalInstances = 1, // Must has default value > 0
        totalInstancesUsed = 0,
        remaining = 0;

    if ($scope.model.novaLimits && $scope.model.novaLimits.maxTotalInstances) {
      maxTotalInstances = $scope.model.novaLimits.maxTotalInstances;
    }

    if ($scope.model.novaLimits && $scope.model.novaLimits.totalInstancesUsed) {
      totalInstancesUsed = $scope.model.novaLimits.totalInstancesUsed;
    }

    $scope.donutSettings = {
      innerRadius: 24,
      outerRadius: 30,
      label: {
        'font-size': '16px',
        'fill': '#1f83c6'
      },
      title: {
        'font-size': '10px'
      }
    };

    $scope.instanceStats = {
      title: gettext('Total Instances'),
      label: '100%',
      data: [
        { label: gettext('Current Usage'), value: 1, color: '#1f83c6' },
        { label: gettext('Added'), value: 1, color: '#81c1e7' },
        { label: gettext('Remaining'), value: 1, color: '#d1d3d4' }
      ]
    };

    $scope.$watch(
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

    $scope.$watch(
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

    $scope.$watch(
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

    $scope.$watch(
      function () {
        return $scope.tableData.allocated.length;
      },
      function (newValue, oldValue) {
        if (newValue !== oldValue) {
          updateChart();
        }
        checkVolumeForImage(newValue);
      }
    );

    function updateChart() {
      // initialize instance_count to 1
      if ($scope.model.newInstanceSpec.instance_count <= 0) {
        $scope.model.newInstanceSpec.instance_count = 1;
      }
      var instance_count = $scope.model.newInstanceSpec.instance_count || 1;

      var data = $scope.instanceStats.data;
      var remaining = Math.max(0, maxTotalInstances - totalInstancesUsed - selection.length * instance_count);

      data[0].value = totalInstancesUsed;
      data[1].value = selection.length * instance_count;
      data[2].value = remaining;
      $scope.instanceStats.label =
        Math.ceil((maxTotalInstances - remaining) * 100 / maxTotalInstances) + '%';
      $scope.instanceStats = angular.extend({}, $scope.instanceStats);
    }

    //
    // Validations
    //

    // If boot source type is 'image' and 'Create New Volume'
    // is checked, set the minimum volume size for validating
    // vol_size field
    function checkVolumeForImage(newLength) {
      var source = selection ? selection[0] : undefined;

      if (source && $scope.currentBootSource === bootSourceTypes.IMAGE) {
        var imageGb = source.size * 1e-9;
        var imageDisk = source.min_disk;
        $scope.minVolumeSize = Math.ceil(Math.max(imageGb, imageDisk));

        var volumeSizeText = gettext('The volume size must be at least %(minVolumeSize)s GB');
        var volumeSizeObj = { minVolumeSize: $scope.minVolumeSize };
        $scope.minVolumeSizeError = interpolate(volumeSizeText, volumeSizeObj, true);
      } else {
        $scope.minVolumeSize = undefined;
      }
    }

    // Update the maximum instance count based on nova limits
    function updateMaxInstanceCount() {
      $scope.maxInstanceCount = maxTotalInstances - totalInstancesUsed;

      var instanceCountText = gettext('The instance count must not exceed your quota available of %(maxInstanceCount)s instances');
      var instanceCountObj = { maxInstanceCount: $scope.maxInstanceCount };
      $scope.instanceCountMaxError = interpolate(instanceCountText, instanceCountObj, true);
    }

    // Validator for boot source type.
    // Instance count must to be 1 if volume selected
    function validateBootSourceType() {
      var bootSourceType = $scope.currentBootSource;
      var instanceCount = $scope.model.newInstanceSpec.instance_count;

      // Field is valid if boot source type is not volume,
      // instance count is blank/undefined (this is an error with instance count)
      // or instance count is 1
      var isValid = bootSourceType !== bootSourceTypes.VOLUME ||
                    !instanceCount ||
                    instanceCount === 1;

      $scope.launchInstanceSourceForm['boot-source-type']
            .$setValidity('bootSourceType', isValid);
    }

    function findSourceById(sources, id) {
      var i = 0, len = sources.length, source;
      for (; i < len; i++) {
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
        $scope.model.newInstanceSpec.source_type = $scope.bootSourcesOptions[0];
        $scope.currentBootSource = $scope.bootSourcesOptions[0].type;
      }
    }

    $scope.$watchCollection(
      function () {
        return $scope.model.images;
      },
      function (newValue, oldValue) {
        $scope.initPromise.then(function () {
          $scope.$applyAsync(function () {
            if ($scope.launchContext.imageId) {
              setSourceImageWithId($scope.launchContext.imageId);
            }
          });
        });
      }
    );

    //
    // initialize
    //

    changeBootSource($scope.bootSourcesOptions[0].type);

    if (!$scope.model.newInstanceSpec.source_type) {
      $scope.model.newInstanceSpec.source_type = $scope.bootSourcesOptions[0];
      $scope.currentBootSource = $scope.bootSourcesOptions[0].type;
    }
  }

  /**
   * @ngdoc controller
   * @name LaunchInstanceSourceHelpCtrl
   * @description
   * The `LaunchInstanceSourceHelpCtrl` controller provides functions for
   * configuring the help text used within the source step of the
   * Launch Instance Wizard.
   *
   */
  module.controller('LaunchInstanceSourceHelpCtrl', [
    LaunchInstanceSourceHelpCtrl
  ]);

  function LaunchInstanceSourceHelpCtrl() {
    var ctrl = this;

    ctrl.title = gettext('Select Source Help');

    ctrl.instanceDetailsTitle = gettext('Instance Details');
    ctrl.instanceDetailsParagraphs = [
      gettext('An instance name is required and used to help you uniquely identify your instance in the dashboard.'),
      gettext('If you select an availability zone and plan to use the boot from volume option, make sure that the availability zone you select for the instance is the same availability zone where your bootable volume resides.')
    ];

    ctrl.instanceSourceTitle = gettext('Instance Source');
    ctrl.instanceSourceParagraphs = [
      gettext('If you want to create an instance that uses ephemeral storage, meaning the instance data is lost when the instance is deleted, then choose one of the following boot sources:'),
      gettext('<li><b>Image</b>: This option uses an image to boot the instance.</li>'),
      gettext('<li><b>Instance Snapshot</b>: This option uses an instance snapshot to boot the instance.</li>'),
      gettext('If you want to create an instance that uses persistent storage, meaning the instance data is saved when the instance is deleted, then select one of the following boot options:'),
      gettext('<li><b>Image (with Create New Volume checked)</b>: This options uses an image to boot the instance, and creates a new volume to persist instance data. You can specify volume size and whether to delete the volume on termination of the instance.</li>'),
      gettext('<li><b>Volume</b>: This option uses a volume that already exists. It does not create a new volume. You can choose to delete the volume on termination of the instance. <em>Note: when selecting Volume, you can only launch one instance.</em></li>'),
      gettext('<li><b>Volume Snapshot</b>: This option uses a volume snapshot to boot the instance, and creates a new volume to persist instance data. You can choose to delete the volume on termination of the instance.</li>')
    ];
  }

})();
