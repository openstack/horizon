/**
 * (c) Copyright 2016 99Cloud
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
   * @ngname horizon.dashboard.identity.users.details
   *
   * @description
   * Provides details features for users.
   */
  angular
    .module('horizon.dashboard.identity.users.details', [
      'horizon.framework.conf',
      'horizon.app.core'
    ])
   .run(registerUserDetails);

  registerUserDetails.$inject = [
    'horizon.dashboard.identity.users.basePath',
    'horizon.dashboard.identity.users.resourceType',
    'horizon.framework.conf.resource-type-registry.service',
    'horizon.dashboard.identity.users.service'
  ];

  function registerUserDetails(
    basePath,
    userResourceType,
    registry,
    usersService
  ) {
    registry.getResourceType(userResourceType)
      .setLoadFunction(usersService.getUserPromise)
      .detailsViews.append({
        id: 'userDetailsOverview',
        name: gettext('Overview'),
        template: basePath + 'details/overview.html'
      });
  }

})();
