/*
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
   * @ngname horizon.dashboard.identity.domains.actions
   *
   * @description
   * Provides all of the actions for domains.
   */
  angular.module('horizon.dashboard.identity.domains.actions', [
    'horizon.dashboard.identity.domains'
  ])
    .run(registerDomainActions);

  registerDomainActions.$inject = [
    'horizon.framework.conf.resource-type-registry.service',
    'horizon.dashboard.identity.domains.actions.create.service',
    'horizon.dashboard.identity.domains.actions.delete.service',
    'horizon.dashboard.identity.domains.resourceType'
  ];

  function registerDomainActions(
    registry,
    createDomainService,
    deleteDomainService,
    domainResourceType
  ) {
    var resourceType = registry.getResourceType(domainResourceType);

    resourceType.globalActions
      .append({
        id: 'createDomainAction',
        service: createDomainService,
        template: {
          text: gettext('Create Domain'),
          type: 'create'
        }
      });
    resourceType.batchActions
      .append({
        id: 'deleteDomainsAction',
        service: deleteDomainService,
        template: {
          text: gettext('Delete Domains'),
          type: 'delete-selected'
        }
      });
    resourceType.itemActions
      .append({
        id: 'deleteDomainAction',
        service: deleteDomainService,
        template: {
          text: gettext('Delete Domain'),
          type: 'delete'
        }
      });
  }

})();
