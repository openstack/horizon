/*
 * (c) Copyright 2016 Hewlett Packard Enterprise Development Company LP
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
(function() {
  'use strict';

  angular
    .module('horizon.framework.widgets.table')
    .controller('horizon.framework.widgets.table.HzDynamicTableController', controller);

  controller.$inject = [
    '$scope',
    'horizon.framework.conf.permissions.service'
  ];

  function controller($scope, permissionsService) {
    // For now, NOT using controller as syntax. See directive definition
    $scope.items = [];
    $scope.columnAllowed = columnAllowed;

    var allowedColumns = {};

    // Deep watch for changes to the table config
    $scope.$watch(
      "config",
      onConfigChange,
      true
    );

    // Local functions

    /**
     * Handle changes to the table config.
     *
     * @param newValue {string}
     * new resource type name
     */
    function onConfigChange (newConfig) {
      if (angular.isDefined(newConfig)) {

        // if selectAll and expand are not set in the config, default set to true
        if (angular.isUndefined(newConfig.selectAll)) {
          newConfig.selectAll = true;
        }
        if (angular.isUndefined(newConfig.expand)) {
          newConfig.expand = true;
        }

        // Check permissions on the columns
        allowedColumns = {};
        angular.forEach(newConfig.columns, checkPermissions);
      }
    }

    function checkPermissions(column) {
      permissionsService.checkAll(column).then(allow, disallow);

      function allow() {
        allowedColumns[column.id] = true;
      }

      function disallow() {
        allowedColumns[column.id] = false;
      }
    }

    /**
     * Returns true if a column is allowed to be shown. Default is false.
     *
     * @param column - The column to check
     * @returns {*|boolean}
     */
    function columnAllowed(column) {
      return allowedColumns[column.id] || false;
    }
  }

})();
