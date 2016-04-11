/**
 *
 * Licensed under the Apache License, Version 2.0 (the "License"); you may
 * not use this file except in compliance with the License. You may obtain
 * a copy of the License at
 *
 *    http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
 * WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
 * License for the specific language governing permissions and limitations
 * under the License.
 */

(function() {
  'use strict';

  angular
      .module('horizon.app.core.images')
      .controller('horizon.app.core.images.steps.CreateVolumeController', CreateVolumeController);

  CreateVolumeController.$inject = [
    '$scope',
    '$filter',
    'horizon.app.core.openstack-service-api.cinder',
    'horizon.app.core.openstack-service-api.nova',
    'horizon.framework.widgets.charts.quotaChartDefaults',
    'horizon.app.core.images.events'
  ];

  /**
  * @ngdoc controller
  * @name horizon.app.core.images.steps.CreateVolumeController
  * @description
  * This controller is use for creating an image.
  */
  function CreateVolumeController($scope, $filter, cinder, nova, quotaChartDefaults, events) {
    var ctrl = this;

    ctrl.volumeType = {};
    ctrl.volumeTypes = [];
    ctrl.availabilityZones = [];
    ctrl.image = $scope.image;
    ctrl.sourceImage = getSourceImage(ctrl.image);
    ctrl.maxTotalVolumeGigabytes = 100;
    ctrl.totalGigabytesUsed = 0;
    ctrl.maxTotalVolumes = 1;
    ctrl.totalVolumesUsed = 0;

    var numberOfVolumesToAdd = 1;

    ctrl.volume = {
      size: 1,
      name: ctrl.image.name,
      description: '',
      volume_type: '',
      availability_zone: '',
      metadata: {},
      image_id: ctrl.image.id,
      snapshot_id: null,
      source_volid: null
    };

    ctrl.storageQuota = {
      title: gettext('Volume and Snapshot Quota (GB)'),
      maxLimit: ctrl.maxTotalVolumeGigabytes,
      label: getPercentUsed(ctrl.volume.size, ctrl.maxTotalVolumeGigabytes),
      data: [
        {
          label: quotaChartDefaults.usageLabel,
          value: ctrl.totalGigabytesUsed,
          colorClass: quotaChartDefaults.usageColorClass
        },
        {
          label: quotaChartDefaults.addedLabel,
          value: ctrl.volume.size,
          colorClass: quotaChartDefaults.addedColorClass
        },
        {
          label: quotaChartDefaults.remainingLabel,
          value: ctrl.maxTotalVolumeGigabytes - ctrl.volume.size,
          colorClass: quotaChartDefaults.remainingColorClass
        }
      ]
    };

    ctrl.volumeQuota = {
      title: gettext('Volume Quota'),
      maxLimit: ctrl.maxTotalVolumes,
      label: getPercentUsed(ctrl.totalVolumesUsed, ctrl.maxTotalVolumes),
      data: [
        {
          label: quotaChartDefaults.usageLabel,
          value: ctrl.totalVolumesUsed,
          colorClass: quotaChartDefaults.usageColorClass
        },
        {
          label: quotaChartDefaults.addedLabel,
          value: numberOfVolumesToAdd,
          colorClass: quotaChartDefaults.addedColorClass
        },
        {
          label: quotaChartDefaults.remainingLabel,
          value: ctrl.maxTotalVolumes - ctrl.totalVolumesUsed,
          colorClass: quotaChartDefaults.remainingColorClass
        }
      ]
    };

    var capacityWatcher = $scope.$watch(
      function() {
        return ctrl.volume.size;
      },
      updateStorageGraph
    );

    var volumeWatcher = $scope.$watch(
      function() {
        return ctrl.volume;
      },
      volumeChangeEvent,
      true
    );

    $scope.$on('$destroy', deregisterWatchers);

    init();

    function init() {
      cinder.getVolumeTypes().success(onGetVolumeTypes);
      cinder.getAbsoluteLimits().success(onGetAbsoluteLimits);
      nova.getAvailabilityZones().success(onGetAvailabilityZones);
    }

    function onGetVolumeTypes(response) {
      ctrl.volumeTypes = response.items;
      cinder.getDefaultVolumeType().success(onGetDefaultVolumeType);
    }

    function onGetDefaultVolumeType(response) {
      ctrl.volumeTypes.forEach(function(volumeType) {
        if (volumeType.name === response.name) {
          ctrl.volumeType = volumeType;
          return;
        }
      });
    }

    function onGetAvailabilityZones(response) {
      ctrl.availabilityZones = response.items;
    }

    function onGetAbsoluteLimits(response) {
      ctrl.maxTotalVolumeGigabytes = response.maxTotalVolumeGigabytes;
      ctrl.totalGigabytesUsed = response.totalGigabytesUsed;
      updateStorageGraph();

      ctrl.totalVolumesUsed = response.totalVolumesUsed;
      ctrl.maxTotalVolumes = response.maxTotalVolumes;
      updateInstanceGraph();
    }

    function updateStorageGraph() {
      if (ctrl.volume.size >= 0) {
        var totalGigabytesAllocated = ctrl.volume.size + ctrl.totalGigabytesUsed;
        ctrl.storageQuota.data[0].value = ctrl.totalGigabytesUsed;
        ctrl.storageQuota.data[1].value = ctrl.volume.size;
        ctrl.storageQuota.data[2].value =
          Math.max(ctrl.maxTotalVolumeGigabytes - totalGigabytesAllocated, 0);
        ctrl.storageQuota.label =
          getPercentUsed(totalGigabytesAllocated,ctrl.maxTotalVolumeGigabytes);
        ctrl.storageQuota.maxLimit = ctrl.maxTotalVolumeGigabytes;
        ctrl.storageQuota.overMax = totalGigabytesAllocated > ctrl.storageQuota.maxLimit;
        ctrl.storageQuota = angular.extend({}, ctrl.storageQuota);
        $scope.volumeForm.$setValidity('volumeSize', !ctrl.storageQuota.overMax);
      }
    }

    function updateInstanceGraph() {
      ctrl.volumeQuota.data[0].value = ctrl.totalVolumesUsed;
      ctrl.volumeQuota.data[2].value =
        Math.max(ctrl.maxTotalVolumes - ctrl.totalVolumesUsed - numberOfVolumesToAdd, 0);
      ctrl.volumeQuota.label = getPercentUsed(ctrl.totalVolumesUsed + numberOfVolumesToAdd,
        ctrl.maxTotalVolumes);
      ctrl.volumeQuota.maxLimit = ctrl.maxTotalVolumes;
      ctrl.volumeQuota.overMax = ctrl.totalVolumesUsed === ctrl.volumeQuota.maxLimit;
      ctrl.volumeQuota = angular.extend({}, ctrl.volumeQuota);
    }

    function getPercentUsed(used, total) {
      return Math.round((used / total) * 100) + '%';
    }

    function getSourceImage(image) {
      return image.name + ' (' + $filter('bytes')(image.size) + ')';
    }

    function volumeChangeEvent() {
      ctrl.volume.volume_type = ctrl.volumeType.name || '';
      $scope.$emit(events.VOLUME_CHANGED, ctrl.volume);
    }

    function deregisterWatchers() {
      capacityWatcher();
      volumeWatcher();
    }
  }
})();
