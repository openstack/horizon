/*
 * Copyright 2016 NEC Corporation.
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
   * @ngname horizon.cluster.receivers.details
   *
   * @description
   * Provides details features for domain.
   */
  angular.module('horizon.dashboard.identity.domains.details', [
    'horizon.framework.conf',
    'horizon.app.core'
  ])
   .run(registerDomainDetails);

  registerDomainDetails.$inject = [
    'horizon.dashboard.identity.domains.basePath',
    'horizon.dashboard.identity.domains.resourceType',
    'horizon.app.core.openstack-service-api.keystone',
    'horizon.framework.conf.resource-type-registry.service'
  ];

  function registerDomainDetails(basePath, domainResourceType, keystone, registry) {
    registry.getResourceType(domainResourceType)
      .setLoadFunction(loadFunction)
      .detailsViews.append({
        id: 'domainDetailsOverview',
        name: gettext('Overview'),
        template: basePath + 'details/overview.html'
      });

    function loadFunction(identifier) {
      return keystone.getDomain(identifier);
    }
  }

})();
