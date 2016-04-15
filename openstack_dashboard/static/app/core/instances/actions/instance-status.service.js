/**
 * (c) Copyright 2016 Hewlett Packard Enterprise Development Company LP
 *
 * Licensed under the Apache License, Version 2.0 (the "License"); you may
 * not use self file except in compliance with the License. You may obtain
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
    .module('horizon.app.core.instances.actions')
    .factory('horizon.app.core.instances.actions.instance-status.service', factory);


  /**
   * @ngDoc factory
   * @name horizon.app.core.instances.actions.instance-status.service
   *
   * @Description
   * Provides useful status-evaluation features.
   */
  function factory(
  ) {

    return {
      isDeleting: isDeleting,
      anyStatus: anyStatus,
      anyPowerState: anyPowerState
    };

    function anyStatus(instance, validStatuses) {
      return valueInList(instance.status, validStatuses);
    }

    function anyPowerState(instance, validStatuses) {
      var powerStates = {
        0: "NO STATE",
        1: "RUNNING",
        2: "BLOCKED",
        3: "PAUSED",
        4: "SHUTDOWN",
        5: "SHUTOFF",
        6: "CRASHED",
        7: "SUSPENDED",
        8: "FAILED",
        9: "BUILDING"
      };
      return valueInList(powerStates[instance['OS-EXT-STS:power_state']], validStatuses);
    }

    function isDeleting(instance) {
      return upperCase(instance['OS-EXT-STS:task_state']) === 'DELETING';
    }

    function valueInList(value, list) {
      return list.indexOf(upperCase(value)) > -1;
    }

    function upperCase(val) {
      return String(val).toUpperCase();
    }
  }
})();
