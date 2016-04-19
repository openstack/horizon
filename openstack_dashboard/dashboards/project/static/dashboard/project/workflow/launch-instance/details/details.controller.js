/*
 * Copyright 2015 Hewlett Packard Enterprise Development Company LP
 * (c) Copyright 2015 ThoughtWorks Inc.
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
   * @name LaunchInstanceDetailsController
   * @description
   * The `LaunchInstanceDetailsController` controller provides functions for
   * configuring the details step of the Launch Instance Wizard.
   *
   */
  angular
    .module('horizon.dashboard.project.workflow.launch-instance')
    .controller('LaunchInstanceDetailsController', LaunchInstanceDetailsController);

  LaunchInstanceDetailsController.$inject = [
    '$scope',
    'horizon.framework.widgets.charts.donutChartSettings',
    'horizon.framework.widgets.charts.quotaChartDefaults',
    'horizon.app.core.openstack-service-api.nova'
  ];

  function LaunchInstanceDetailsController($scope,
    donutChartSettings,
    quotaChartDefaults,
    novaAPI
  ) {

    var ctrl = this;
    novaAPI.isFeatureSupported(
      'instance_description').then(isDescriptionSupported);

    // Error text for invalid fields
    ctrl.instanceNameError = gettext('A name is required for your instance.');
    ctrl.instanceCountError = gettext(
      'Instance count is required and must be an integer of at least 1'
    );
    ctrl.maxInstanceCount = 1;

    /*
     * Donut chart
     */
    ctrl.chartSettings = donutChartSettings;
    ctrl.maxInstances = 1; // Must have default value > 0
    ctrl.totalInstancesUsed = 0;

    if ($scope.model.novaLimits && $scope.model.novaLimits.maxTotalInstances) {
      ctrl.maxInstances = $scope.model.novaLimits.maxTotalInstances;
    }

    if ($scope.model.novaLimits && $scope.model.novaLimits.totalInstancesUsed) {
      ctrl.totalInstancesUsed = $scope.model.novaLimits.totalInstancesUsed;
    }

    ctrl.instanceStats = {
      title: gettext('Total Instances'),
      maxLimit: ctrl.maxInstances,
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

    syncInstanceChartAndLimits();

    var specifiedInstancesWatcher = createWatcher(getInstanceCount, updateChart);
    var maxInstancesWatcher = createWatcher(getMaxInstances, resetMaxInstances);
    var instancesUsedWatcher = createWatcher(getTotalInstancesUsed, resetTotalInstancesUsed);

    // Explicitly remove watchers on desruction of this controller
    $scope.$on('$destroy', function() {
      specifiedInstancesWatcher();
      maxInstancesWatcher();
      instancesUsedWatcher();
    });

    ////////////////////

    function isDescriptionSupported(data) {
      ctrl.isDescriptionSupported = data.data;
    }

    function getMaxInstances() {
      return $scope.model.novaLimits.maxTotalInstances;
    }

    function resetMaxInstances(newMaxInstances) {
      ctrl.maxInstances = Math.max(1, newMaxInstances);
      syncInstanceChartAndLimits();
    }

    function getTotalInstancesUsed() {
      return $scope.model.novaLimits.totalInstancesUsed;
    }

    function resetTotalInstancesUsed() {
      ctrl.totalInstancesUsed = $scope.model.novaLimits.totalInstancesUsed;
      syncInstanceChartAndLimits();
    }

    function getInstanceCount() {
      return $scope.model.newInstanceSpec.instance_count;
    }

    function createWatcher(watchExpression, listener) {
      return $scope.$watch(
        watchExpression,
        function (newValue, oldValue) {
          if (newValue !== oldValue) {
            listener(newValue);
          }
        }
      );
    }

    function syncInstanceChartAndLimits() {
      updateChart();
      updateMaxInstanceCount();
    }

    function updateChart() {

      // Initialize instance_count to 1
      if ($scope.model.newInstanceSpec.instance_count <= 0) {
        $scope.model.newInstanceSpec.instance_count = 1;
      }

      var data = ctrl.instanceStats.data;
      var added = $scope.model.newInstanceSpec.instance_count || 1;
      var remaining = Math.max(0, ctrl.maxInstances - ctrl.totalInstancesUsed - added);

      ctrl.instanceStats.maxLimit = ctrl.maxInstances;
      data[0].value = ctrl.totalInstancesUsed;
      data[1].value = added;
      data[2].value = remaining;
      var quotaCalc = Math.round((ctrl.totalInstancesUsed + added) / ctrl.maxInstances * 100);
      ctrl.instanceStats.overMax = quotaCalc > 100;
      ctrl.instanceStats.label = quotaCalc + '%';
      ctrl.instanceStats = angular.extend({}, ctrl.instanceStats);
    }

    /*
     * Validation
     */

    // Update the maximum instance count based on nova limits
    function updateMaxInstanceCount() {
      ctrl.maxInstanceCount = ctrl.maxInstances - ctrl.totalInstancesUsed;

      var instanceCountText = gettext(
        'The instance count must not exceed your quota available of %(maxInstanceCount)s instances'
      );
      var instanceCountObj = { maxInstanceCount: ctrl.maxInstanceCount };
      ctrl.instanceCountMaxError = interpolate(instanceCountText, instanceCountObj, true);
    }

  }
})();
