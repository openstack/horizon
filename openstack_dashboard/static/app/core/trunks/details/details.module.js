/*
 * Copyright 2017 Ericsson
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
   * @ngname horizon.app.core.trunks.details
   *
   * @description
   * Provides details features for trunks.
   */
  angular
    .module('horizon.app.core.trunks.details', [
      'horizon.framework.conf',
      'horizon.app.core'
    ])
   .run(registerTrunkDetails);

  registerTrunkDetails.$inject = [
    'horizon.app.core.trunks.basePath',
    'horizon.app.core.trunks.resourceType',
    'horizon.app.core.trunks.service',
    'horizon.framework.conf.resource-type-registry.service'
  ];

  function registerTrunkDetails(
    basePath,
    trunkResourceType,
    trunkService,
    registry
  ) {
    registry.getResourceType(trunkResourceType)
      .setLoadFunction(trunkService.getTrunkPromise)
      .detailsViews.append({
        id: 'trunkDetailsOverview',
        name: gettext('Overview'),
        template: basePath + 'details/overview.html'
      });
  }

})();
