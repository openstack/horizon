/**
 * Copyright 2016 99Cloud
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
   * @ngname horizon.dashboard.identity.roles
   *
   * @description
   * Provides all of the services and widgets required
   * to support and display roles related content.
   */
  angular
    .module('horizon.dashboard.identity.roles', [
      'ngRoute',
      'horizon.dashboard.identity.roles.actions'
    ])
    .constant('horizon.dashboard.identity.roles.resourceType', 'OS::Keystone::Role')
    .run(run)
    .config(config);

  run.$inject = [
    'horizon.framework.conf.resource-type-registry.service',
    'horizon.app.core.openstack-service-api.keystone',
    'horizon.dashboard.identity.roles.resourceType'
  ];

  function run(registry, keystone, roleResourceType) {
    registry.getResourceType(roleResourceType)
      .setNames('Role', 'Roles', ngettext('Role', 'Roles', 1))
      .setProperties(roleProperties())
      .setListFunction(listFunction)
      .tableColumns
      .append({
        id: 'name',
        priority: 1,
        sortDefault: true,
        classes: "word-wrap"
      })
      .append({
        id: 'id',
        priority: 1
      });

    function listFunction() {
      return keystone.getRoles().then(addTrackBy);
    }

    // We need to modify the API's response by adding a composite value called
    // 'trackBy' to assist the display mechanism when updating rows.
    function addTrackBy(response) {
      return {data: {items: response.data.items.map(function(role) {
        role.trackBy = [
          role.id,
          role.domain_id,
          role.name
        ].join('/');
        return role;
      })}};
    }

    function roleProperties() {
      return {
        name: { label: gettext('Name'), filters: ['noName'] },
        id: { label: gettext('ID'), filters: ['noValue'] }
      };
    }
  }

  config.$inject = [
    '$provide',
    '$windowProvider',
    '$routeProvider'
  ];

  function config($provide, $windowProvider, $routeProvider) {
    var path = $windowProvider.$get().STATIC_URL + 'dashboard/identity/roles/';
    $provide.constant('horizon.dashboard.identity.roles.basePath', path);

    $routeProvider.when('/identity/roles', {
      templateUrl: path + 'panel.html'
    });
  }
})();
