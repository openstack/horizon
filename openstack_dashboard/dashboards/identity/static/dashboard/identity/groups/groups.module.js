/**
 * Copyright 2017 99Cloud
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
   * @ngname horizon.dashboard.identity.groups
   *
   * @description
   * Provides all of the services and widgets required
   * to support and display groups related content.
   */
  angular
    .module('horizon.dashboard.identity.groups', [
      'ngRoute',
      'horizon.dashboard.identity.groups.actions'
    ])
    .constant('horizon.dashboard.identity.groups.resourceType', 'OS::Keystone::Group')
    .run(run)
    .config(config);

  run.$inject = [
    'horizon.framework.conf.resource-type-registry.service',
    'horizon.app.core.openstack-service-api.keystone',
    'horizon.dashboard.identity.groups.basePath',
    'horizon.dashboard.identity.groups.resourceType'
  ];

  function run(registry, keystone, basePath, groupResourceType) {
    registry.getResourceType(groupResourceType)
      .setNames('Group', 'Groups', ngettext('Group', 'Groups', 1))
      .setProperties(groupProperties())
      .setListFunction(listFunction)
      .tableColumns
      .append({
        id: 'name',
        priority: 1,
        sortDefault: true
      })
      .append({
        id: 'description',
        priority: 1
      })
      .append({
        id: 'id',
        priority: 1
      });

    registry.getResourceType(groupResourceType).filterFacets
      .append({
        label: gettext('Name'),
        name: 'name',
        singleton: true
      })
      .append({
        label: gettext('ID'),
        name: 'id',
        singleton: true
      });

    function listFunction() {
      return keystone.getGroups().then(modifyResponse);
    }

    function modifyResponse(response) {
      return {data: {items: response.data.items.map(modifyItem)}};

      function modifyItem(item) {
        item.trackBy = item.id + item.domain_id + item.name + item.description;
        return item;
      }
    }

    /**
     * @name groupProperties
     * @description resource properties for group module
     */
    function groupProperties() {
      return {
        name: {
          label: gettext('Name'),
          filters: ['noName']
        },
        description: {
          label: gettext('Description'),
          filters: ['noValue']
        },
        id: {
          label: gettext('ID'),
          filters: ['noValue']
        }
      };
    }
  }

  config.$inject = [
    '$provide',
    '$windowProvider',
    '$routeProvider'
  ];

  /**
   * @name config
   * @param {Object} $provide
   * @param {Object} $windowProvider
   * @param {Object} $routeProvider
   * @description Routes used by this module.
   * @returns {undefined} Returns nothing
   */
  function config($provide, $windowProvider, $routeProvider) {
    var path = $windowProvider.$get().STATIC_URL + 'dashboard/identity/groups/';
    $provide.constant('horizon.dashboard.identity.groups.basePath', path);

    $routeProvider.when('/identity/groups', {
      templateUrl: path + 'panel.html'
    });
  }
})();
