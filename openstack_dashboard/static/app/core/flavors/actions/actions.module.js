/**
 * (c) Copyright 2016 Hewlett-Packard Development Company, L.P.
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

  /**
   * @ngdoc overview
   * @ngname horizon.app.core.flavors.actions
   *
   * @description
   * Provides all of the actions for flavors.
   */
  angular.module('horizon.app.core.flavors.actions', [
    'horizon.framework.conf',
    'horizon.app.core.flavors'
  ])
    .run(registerFlavorActions);

  registerFlavorActions.$inject = [
    'horizon.framework.conf.resource-type-registry.service',
    'horizon.app.core.flavors.actions.delete-flavor.service',
    'horizon.app.core.flavors.actions.update-metadata.service',
    'horizon.app.core.flavors.resourceType'
  ];

  function registerFlavorActions(
    registry,
    deleteFlavorService,
    updateMetadataService,
    flavorResourceTypeCode
  ) {
    var flavorResourceType = registry.getResourceType(flavorResourceTypeCode);
    flavorResourceType.itemActions
      .append({
        id: 'updateMetadataService',
        service: updateMetadataService,
        template: {
          text: gettext('Update Metadata')
        }
      })
      .append({
        id: 'deleteFlavorAction',
        service: deleteFlavorService,
        template: {
          type: 'delete',
          text: gettext('Delete Flavor')
        }
      });

    flavorResourceType.batchActions
      .append({
        id: 'batchDeleteFlavorAction',
        service: deleteFlavorService,
        template: {
          type: 'delete-selected',
          text: gettext('Delete Flavors')
        }
      });
  }

})();
