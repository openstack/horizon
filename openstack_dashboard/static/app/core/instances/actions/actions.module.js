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
   * @ngname horizon.app.core.instances.actions
   *
   * @description
   * Provides all of the actions for instances.
   */
  angular.module('horizon.app.core.instances.actions',
    ['horizon.framework.conf', 'horizon.app.core'])
    .run(run);

  run.$inject = [
    'horizon.framework.conf.resource-type-registry.service',
    'horizon.framework.util.actions.redirect-action.service',
    'horizon.app.core.images.actions.launch-instance.service',
    'horizon.app.core.instances.actions.delete-instance.service',
    'horizon.app.core.instances.actions.start.service',
    'horizon.app.core.instances.actions.stop.service',
    'horizon.app.core.instances.resourceType'
  ];

  function run(
    registry,
    redirectService,
    launchInstanceService,
    deleteService,
    startService,
    stopService,
    instanceResourceTypeCode)
  {
    var instanceResourceType = registry.getResourceType(instanceResourceTypeCode);
    instanceResourceType.globalActions
      .append({
        id: 'launchInstanceService',
        service: launchInstanceService,
        template: {
          text: gettext('Create Instance')
        }
      });
    instanceResourceType.itemActions
      .append({
        id: 'startService',
        service: startService,
        template: {
          text: gettext('Start')
        }
      })
      .append({
        id: 'stopService',
        service: stopService,
        template: {
          text: gettext('Stop')
        }
      })
      .append({
        id: 'legacyService',
        service: redirectService(legacyPath),
        template: {
          text: gettext('Legacy Details...')
        }
      })
      .append({
        id: 'deleteService',
        service: deleteService,
        template: {
          type: 'delete',
          text: gettext('Delete')
        }
      });

   function legacyPath(item) {
     return 'project/instances/' + item.id + '/';
   }
  }

})();
