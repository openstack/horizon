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
   * @ngname horizon.app.core.network_qos.details
   *
   * @description
   * Provides details features for policies.
   */
  angular
    .module('horizon.app.core.network_qos.details', [
      'horizon.framework.conf',
      'horizon.app.core'
    ])
    .run(registerPolicyDetails);

  registerPolicyDetails.$inject = [
    'horizon.app.core.network_qos.basePath',
    'horizon.app.core.network_qos.resourceType',
    'horizon.app.core.network_qos.service',
    'horizon.framework.conf.resource-type-registry.service'
  ];

  function registerPolicyDetails(
    basePath,
    qosResourceType,
    qosService,
    registry
  ) {
    registry.getResourceType(qosResourceType)
      .setLoadFunction(qosService.getPolicyPromise)
      .detailsViews.append({
        id: 'policyDetailsOverview',
        name: gettext('Overview'),
        template: basePath + 'details/overview.html'
      });
  }

})();
