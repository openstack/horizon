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
    .module('horizon.app.core.instances')
    .factory('horizon.app.core.instances.actions.hard-reboot.service', factory);

  factory.$inject = [
    'horizon.app.core.openstack-service-api.nova',
    'horizon.app.core.instances.actions.generic-simple.service'
  ];

  /**
   * @ngDoc factory
   * @name horizon.app.core.instances.actions.hard-reboot.service
   *
   * @Description
   * Hard-reboots the instance
   */
  function factory(nova, simpleService) {

    var config = {
      rules: [],
      execute: execute,
      validState: validState
    };

    return simpleService(config);

    function execute(instance) {
      return nova.hardRebootServer(instance.id);
    }

    function validState(instance) {
      return !instance.protected &&
        (instance.status === 'ACTIVE' || instance.status === 'SHUTOFF') &&
        instance['OS-EXT-STS:task_state'] !== 'DELETING';
    }
  }
})();
