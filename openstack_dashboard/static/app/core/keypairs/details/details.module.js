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
   * @ngname horizon.app.core.keypairs.details
   *
   * @description
   * Provides details features for keypair.
   */
  angular.module('horizon.app.core.keypairs.details',
                 ['horizon.framework.conf', 'horizon.app.core'])
  .run(registerKeypairDetails);

  registerKeypairDetails.$inject = [
    'horizon.app.core.keypairs.basePath',
    'horizon.app.core.keypairs.resourceType',
    'horizon.app.core.keypairs.service',
    'horizon.framework.conf.resource-type-registry.service'
  ];

  function registerKeypairDetails(
    basePath,
    resourceType,
    keypairService,
    registry
  ) {
    registry.getResourceType(resourceType)
      .setLoadFunction(keypairService.getKeypairPromise)
      .detailsViews.append({
        id: 'keypairDetails',
        name: gettext('Details'),
        template: basePath + 'details/details.html'
      });
  }

})();
