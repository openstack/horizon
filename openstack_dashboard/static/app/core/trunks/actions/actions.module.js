/*
 * Copyright 2017 Ericsson
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *    http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

(function() {
  'use strict';

  /**
   * @ngdoc overview
   * @ngname horizon.app.core.trunks.actions
   *
   * @description
   * Provides all trunk actions.
   */
  angular.module('horizon.app.core.trunks.actions', [
    'horizon.framework.conf',
    'horizon.app.core.trunks'
  ])

  .run(registerTrunkActions);

  registerTrunkActions.$inject = [
    'horizon.framework.conf.resource-type-registry.service',
    'horizon.app.core.trunks.actions.create.service',
    'horizon.app.core.trunks.actions.edit.service',
    'horizon.app.core.trunks.actions.delete.service',
    'horizon.app.core.trunks.resourceType'
  ];

  function registerTrunkActions(
    registry,
    createService,
    editService,
    deleteService,
    trunkResourceTypeCode
  ) {
    var trunkResourceType = registry.getResourceType(trunkResourceTypeCode);

    trunkResourceType.globalActions
      .append({
        id: 'createTrunkAction',
        service: createService,
        template: {
          text: gettext('Create Trunk'),
          type: 'create'
        }
      });

    trunkResourceType.itemActions
      .append({
        id: 'editTrunkAction',
        service: editService,
        template: {
          text: gettext('Edit Trunk')
        }
      })
      .append({
        id: 'deleteTrunkAction',
        service: deleteService,
        template: {
          text: gettext('Delete Trunk'),
          type: 'delete'
        }
      });

    trunkResourceType.batchActions
      .append({
        id: 'batchDeleteTrunkAction',
        service: deleteService,
        template: {
          text: gettext('Delete Trunks'),
          type: 'delete-selected'
        }
      });

  }

})();
