/**
 * Copyright 2015 IBM Corp.
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
   * @ngname horizon.dashboard.identity.users
   *
   * @description
   * Provides all of the services and widgets required
   * to support and display users related content.
   */
  angular
    .module('horizon.dashboard.identity.users', [
      'ngRoute'
    ])
    .constant('horizon.dashboard.identity.users.resourceType', 'OS::Keystone::User')
    .run(run)
    .config(config);

  run.$inject = [
    'horizon.framework.conf.resource-type-registry.service',
    'horizon.app.core.openstack-service-api.keystone',
    'horizon.dashboard.identity.users.basePath',
    'horizon.dashboard.identity.users.resourceType'
  ];

  function run(registry, keystone, basePath, userResourceType) {
    registry.getResourceType(userResourceType)
      .setNames(gettext('User'), gettext('Users'))
      .setSummaryTemplateUrl(basePath + 'details/drawer.html')
      .setProperties(userProperties())
      .setListFunction(listFunction)
      .tableColumns
      .append({
        id: 'name',
        priority: 1,
        sortDefault: true,
        urlFunction: urlFunction
      })
      .append({
        id: 'email',
        priority: 2,
        filters: ['noValue'],
        template: '<a ng-href="mailto:{$ item.email $}">{$ item.email $}</a>'
      })
      .append({
        id: 'id',
        priority: 1
      })
      .append({
        id: 'enabled',
        priority: 2,
        filters: ['yesno']
      });

    registry.getResourceType(userResourceType).filterFacets
      .append({
        label: gettext('Name'),
        name: 'name',
        singleton: true
      })
      .append({
        label: gettext('Email'),
        name: 'email',
        singleton: true
      })
      .append({
        label: gettext('ID'),
        name: 'id',
        singleton: true
      })
      .append({
        label: gettext('Enabled'),
        name: 'enabled',
        singleton: true,
        options: [
          {label: gettext('Yes'), key: 'true'},
          {label: gettext('No'), key: 'false'}
        ]
      });

    function listFunction() {
      return keystone.getUsers();
    }

    function urlFunction(item) {
      return 'identity/ngdetails/OS::Keystone::User/' + item.id;
    }

    /**
     * @name userProperties
     * @description resource properties for user module
     */
    function userProperties() {
      return {
        name: gettext('Name'),
        email: gettext('Email'),
        id: gettext('ID'),
        enabled: gettext('Enabled'),
        domain_id: gettext('Domain ID'),
        domain_name: gettext('Domain Name'),
        description: gettext('Description'),
        project_id: gettext('Primary Project ID')
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
    var path = $windowProvider.$get().STATIC_URL + 'dashboard/identity/users/';
    $provide.constant('horizon.dashboard.identity.users.basePath', path);

    $routeProvider.when('/identity/users', {
      templateUrl: path + 'panel.html'
    });
  }
})();
