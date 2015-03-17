(function () {
  'use strict';

  var module = angular.module('hz.dashboard.launch-instance');

  module.controller('LaunchInstanceSourceCtrl', [
    '$scope',
    'bytesFilter',
    LaunchInstanceSourceCtrl
  ]);

  module.controller('LaunchInstanceSourceHelpCtrl', [
    '$scope',
    LaunchInstanceSourceHelpCtrl
  ]);

  function LaunchInstanceSourceCtrl($scope, bytesFilter) {

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
      volume: {
        available: $scope.model.volumes,
        allocated: selection,
        displayedAvailable: [],
        displayedAllocated: selection
      },
      snapshot: {
        available: $scope.model.imageSnapshots,
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

    var tableHeadCellsMap = {
      image: [
        { text: gettext('Name'), style: { width: '25%' } },
        { text: gettext('Updated'), style: { width: '20%' } },
        { text: gettext('Size'), style: { width: '15%' }, classList: ['number'] },
        { text: gettext('Type') }
      ],
      volume: [
        { text: gettext('Name'), style: { width: '25%' } },
        { text: gettext('Type'), style: { width: '20%' } },
        { text: gettext('Size'), classList: ['number'] }
      ],
      snapshot: [
        { text: gettext('Name'), style: { width: '25%' } },
        { text: gettext('Type'), style: { width: '20%' } },
        { text: gettext('Size'), classList: ['number'] }
      ],
      volume_snapshot: [
        { text: gettext('Name'), style: { width: '25%' } },
        { text: gettext('Type'), style: { width: '20%' } },
        { text: gettext('Size'), classList: ['number'] }
      ]
    };

    var tableBodyCellsMap = {
      image: [
        { key: 'name', classList: ['hi-light'] },
        { key: 'updated_at' },
        { key: 'size', filter: bytesFilter, classList: ['number'] },
        { key: 'disk_format', style: { 'text-transform': 'uppercase' } }
      ],
      volume: [
        { key: 'name', classList: ['hi-light'] },
        { key: 'disk_format', style: { 'text-transform': 'uppercase' } },
        { key: 'size', filter: bytesFilter, classList: ['number'] }
      ],
      snapshot: [
        { key: 'name', classList: ['hi-light'] },
        { key: 'disk_format', style: { 'text-transform': 'uppercase' } },
        { key: 'size', filter: bytesFilter, classList: ['number'] }
      ],
      volume_snapshot: [
        { key: 'name', classList: ['hi-light'] },
        { key: 'disk_format', style: { 'text-transform': 'uppercase' } },
        { key: 'size', filter: bytesFilter, classList: ['number'] }
      ]
    };

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
        availHelpText: gettext('Select one.')
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
        'color': '#1f83c6'
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
        (maxTotalInstances - remaining) * 100 / maxTotalInstances + '%';
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

  function LaunchInstanceSourceHelpCtrl($scope) {
    $scope.title = gettext('Instance Details Help');
    $scope.content = gettext('This is the help text.');
  }

})();
