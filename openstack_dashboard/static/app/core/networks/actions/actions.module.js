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
   * @ngname horizon.app.core.networks.actions
   *
   * @description
   * Provides all of the actions for networks.
   */
  angular.module('horizon.app.core.networks.actions',
    ['horizon.framework.conf', 'horizon.app.core', 'horizon.framework.util.actions'])
    .run(run);

  run.$inject = [
    'horizon.framework.conf.resource-type-registry.service',
    'horizon.framework.util.actions.redirect-action.service',
    'horizon.app.core.networks.resourceType'
  ];

  function run(
    registry,
    redirectService,
    resourceType)
  {
    var instanceResourceType = registry.getResourceType(resourceType);
    instanceResourceType.itemActions
      .append({
        id: 'legacyService',
        service: redirectService(legacyPath),
        template: {
          text: gettext('More Details...')
        }
      });

    function legacyPath(item) {
     return 'project/networks/' + item.id + '/detail';
    }
  }

})();
