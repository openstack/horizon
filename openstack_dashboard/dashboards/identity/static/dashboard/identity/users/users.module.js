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
      'ngRoute',
      'horizon.dashboard.identity.users.details',
      'horizon.dashboard.identity.users.actions'
    ])
    .constant('horizon.dashboard.identity.users.resourceType', 'OS::Keystone::User')
    .constant('horizon.dashboard.identity.users.validationRules', validationRules())
    .run(run)
    .config(config);

  run.$inject = [
    'horizon.framework.conf.resource-type-registry.service',
    'horizon.dashboard.identity.users.basePath',
    'horizon.dashboard.identity.users.resourceType',
    'horizon.dashboard.identity.users.service'
  ];

  function run(registry, basePath, userResourceType, usersService) {
    registry.getResourceType(userResourceType)
      .setNames('User', 'Users', ngettext('User', 'Users', 1))
      .setSummaryTemplateUrl(basePath + 'details/drawer.html')
      .setDefaultIndexUrl('/identity/users/')
      .setProperties(userProperties())
      .setListFunction(usersService.getUsersPromise)
      .setNeedsFilterFirstFunction(usersService.getFilterFirstSettingPromise)
      .tableColumns
      .append({
        id: 'name',
        priority: 1,
        sortDefault: true,
        urlFunction: usersService.getDetailsPath
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
        singleton: true,
        isServer: true
      })
      .append({
        label: gettext('Email'),
        name: 'email',
        singleton: true
      })
      .append({
        label: gettext('ID'),
        name: 'id',
        singleton: true,
        isServer: true
      })
      .append({
        label: gettext('Enabled'),
        name: 'enabled',
        singleton: true,
        isServer: true,
        options: [
          {label: gettext('Yes'), key: 'true'},
          {label: gettext('No'), key: 'false'}
        ]
      });

    /**
     * @name userProperties
     * @description resource properties for user module
     */
    function userProperties() {
      return {
        name: gettext('Name'),
        email: {label: gettext('Email'), filters: ['noValue']},
        id: gettext('ID'),
        enabled: {label: gettext('Enabled'), filters: ['yesno']},
        domain_id: {label: gettext('Domain ID'), filters: ['noValue']},
        domain_name: {label: gettext('Domain Name'), filters: ['noValue']},
        description: {label: gettext('Description'), filters: ['noValue']},
        default_project_id: {label: gettext('Primary Project ID'), filters: ['noValue']},
        project_name: {label: gettext('Primary Project Name'), filters: ['noValue']}
      };
    }
  }

  /**
   * @ngdoc constant
   * @name horizon.dashboard.identity.users.events.validationRules
   * @description constants for use in validation fields
   */
  function validationRules() {
    return {
      integer: /^[0-9]+$/,
      validatePassword: /.*/,
      fieldMaxLength: 255
    };
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
