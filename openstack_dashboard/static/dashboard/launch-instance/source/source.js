(function () {
  'use strict';

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
    'bytesFilter',
    'dateFilter',
    'decodeFilter',
    'diskFormatFilter',
    'gbFilter',
    'yesnoFilter',
    LaunchInstanceSourceCtrl
  ]);

  function LaunchInstanceSourceCtrl($scope,
                                    bytesFilter,
                                    dateFilter,
                                    decodeFilter,
                                    diskFormatFilter,
                                    gbFilter,
                                    yesnoFilter) {

    $scope.label = {
      title: gettext('Instance Details'),
      subtitle: gettext(''),
      instanceName: gettext('Instance Name'),
      availabilityZone: gettext('Availability Zone'),
      instance_count: gettext('Count'),
      instanceSourceTitle: gettext('Instance Source'),
      instanceSourceSubTitle: gettext(''),
      bootSource: gettext('Select Boot Source'),
      deviceSize: gettext('Device Size (GB)'),
      volumeSize: gettext('Volume Size (GB)'),
      volumeCreate: gettext('Create New Volume'),
      deleteVolumeOnTerminate: gettext('Delete Volume on Terminate'),
      id: gettext('ID')
    };


    //
    // Boot Sources
    //

    $scope.bootSourcesOptions = [
      { type: 'image', label: gettext('Image') },
      { type: 'snapshot', label: gettext('Instance Snapshot') },
      { type: 'volume', label: gettext('Volume') },
      { type: 'volume_snapshot', label: gettext('Volume Snapshot') }
    ];

    $scope.updateBootSourceSelection = function (selectedSource) {
      $scope.currentBootSource = selectedSource.type;
      $scope.model.newInstanceSpec.vol_create = false;
      $scope.model.newInstanceSpec.vol_delete_on_terminate = false;
      changeBootSource(selectedSource.type);
    };

    //
    // Transfer table
    //

    $scope.tableHeadCells = [];
    $scope.tableBodyCells= [];
    $scope.tableData = {};
    $scope.helpText = {};

    var selection = $scope.model.newInstanceSpec.source;

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
        { text: gettext('Encrypted'), style: { width: '20%' }, sortable: true }
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
    var _visibilitymap = {true: gettext('Public'), false: gettext('Private')};

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
        { key: 'encrypted', filter: yesnoFilter }
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
    function changeBootSource(key) {
      updateDataSource(key);
      updateHelpText(key);
      updateTableHeadCells(key);
      updateTableBodyCells(key);
      updateChart();
    }

    function updateDataSource(key) {
      angular.extend($scope.tableData, bootSources[key]);
      selection.length = 0;
    }

    function updateHelpText(key) {
      angular.extend($scope.helpText, {
        noneAllocText: gettext('Select a source from those listed below.'),
        availHelpText: gettext('Select one')
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
      // If a user has entered a count that will result in them exceeding their
      // quota, automatically decrease the count so that it stays within quota
      if (instance_count + totalInstancesUsed > maxTotalInstances) {
        $scope.model.newInstanceSpec.instance_count = maxTotalInstances - totalInstancesUsed;
      }

      data[0].value = totalInstancesUsed;
      data[1].value = selection.length * instance_count;
      data[2].value = remaining;
      $scope.instanceStats.label =
        Math.round((maxTotalInstances - remaining) * 100 / maxTotalInstances) + '%';
      $scope.instanceStats = angular.extend({}, $scope.instanceStats);
    }


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
