/*
 * Copyright 2016 NEC Corporation.
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
   * @ngname horizon.dashboard.identity.domains
   *
   * @description
   * Provides all of the services and widgets required
   * to support and display domains related content.
   */
  angular
    .module('horizon.dashboard.identity.domains', [
      'ngRoute',
      'horizon.dashboard.identity.domains.details',
      'horizon.dashboard.identity.domains.actions'
    ])
    .constant('horizon.dashboard.identity.domains.resourceType', 'OS::Keystone::Domain')
    .run(run)
    .config(config);

  run.$inject = [
    'horizon.framework.conf.resource-type-registry.service',
    'horizon.dashboard.identity.domains.service',
    'horizon.dashboard.identity.domains.basePath',
    'horizon.dashboard.identity.domains.resourceType'
  ];

  function run(registry, domainService, basePath, domainResourceType) {
    registry.getResourceType(domainResourceType)
      .setNames('Domain', 'Domains', ngettext('Domain', 'Domains', 1))
      .setSummaryTemplateUrl(basePath + 'details/drawer.html')
      .setDefaultIndexUrl('/identity/domains/')
      .setProperties(domainProperties())
      .setListFunction(domainService.listDomains)
      .tableColumns
      .append({
        id: 'name',
        priority: 1,
        sortDefault: true,
        urlFunction: domainService.getDetailsPath
      })
      .append({
        id: 'description',
        priority: 1
      })
      .append({
        id: 'id',
        priority: 1
      })
      .append({
        id: 'enabled',
        priority: 1
      });
  }

  function domainProperties() {
    return {
      name: { label: gettext('Name'), filters: ['noName'] },
      description: { label: gettext('Description'), filters: ['noValue'] },
      id: { label: gettext('ID'), filters: ['noValue'] },
      enabled: { label: gettext('Enabled'), filters: ['yesno'] }
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
    var path = $windowProvider.$get().STATIC_URL + 'dashboard/identity/domains/';
    $provide.constant('horizon.dashboard.identity.domains.basePath', path);

    $routeProvider.when('/identity/domains', {
      templateUrl: path + 'panel.html'
    });
  }
})();
