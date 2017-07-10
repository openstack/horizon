/**
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

  /**
   * @ngdoc overview
   * @ngname horizon.app.core.keypairs.actions
   *
   * @description
   * Provides all of the actions for keypairs.
   */
  angular.module('horizon.app.core.keypairs.actions', [
    'horizon.framework.conf',
    'horizon.app.core.keypairs'
  ])
    .run(registerKeypairActions);

  registerKeypairActions.$inject = [
    'horizon.framework.conf.resource-type-registry.service',
    'horizon.app.core.keypairs.actions.delete.service',
    'horizon.app.core.keypairs.resourceType'
  ];

  function registerKeypairActions(
    registry,
    deleteKeypairService,
    resourceType
  ) {
    var keypairResourceType = registry.getResourceType(resourceType);
    keypairResourceType.batchActions
      .append({
        id: 'batchDeleteKeypairAction',
        service: deleteKeypairService,
        template: {
          type: 'delete-selected',
          text: gettext('Delete Key Pairs')
        }
      });
    keypairResourceType.itemActions
      .append({
        id: 'deleteKeypairAction',
        service: deleteKeypairService,
        template: {
          type: 'delete',
          text: gettext('Delete Key Pair')
        }
      });
  }
})();
