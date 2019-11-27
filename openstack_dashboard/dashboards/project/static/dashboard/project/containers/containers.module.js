/**
 *    (c) Copyright 2015 Rackspace, US, Inc.
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
   * @ngname horizon.dashboard.project.containers
   *
   * @description
   * Provides the services and widgets required
   * to support and display the project containers panel.
   */
  angular
    .module('horizon.dashboard.project.containers', [
      'ngRoute',
      'horizon.framework',
      'horizon.app.core.openstack-service-api'
    ])
    .constant('horizon.dashboard.project.containers.account.resourceType', 'OS::Swift::Account')
    .constant('horizon.dashboard.project.containers.container.resourceType', 'OS::Swift::Container')
    .constant('horizon.dashboard.project.containers.object.resourceType', 'OS::Swift::Object')
    .config(config)
    .run(run);

  config.$inject = [
    '$provide',
    '$routeProvider',
    '$windowProvider'
  ];

  /**
   * @name horizon.dashboard.project.containers.basePath
   * @description Base path for the project dashboard
   */
  function config($provide, $routeProvider, $windowProvider) {
    var path = $windowProvider.$get().STATIC_URL + 'dashboard/project/containers/';
    $provide.constant('horizon.dashboard.project.containers.basePath', path);

    var baseRoute = 'project/containers/';
    $provide.constant('horizon.dashboard.project.containers.baseRoute', baseRoute);

    // we include an additional level of URL here to allow for swift service
    // user interaction outside of the scope of containers
    var containerRoute = baseRoute + 'container/';
    $provide.constant('horizon.dashboard.project.containers.containerRoute', containerRoute);

    $routeProvider
      .when('/' + baseRoute, {
        templateUrl: path + 'select-container.html'
      })
      .when('/' + containerRoute, {
        templateUrl: path + 'select-container.html'
      })
      .when('/' + containerRoute + ':container', {
        templateUrl: path + 'objects.html'
      })
      .when('/' + containerRoute + ':container/:folder*', {
        templateUrl: path + 'objects.html'
      });
  }

  run.$inject = [
    'horizon.dashboard.project.containers.account.resourceType',
    'horizon.dashboard.project.containers.container.resourceType',
    'horizon.dashboard.project.containers.object.resourceType',
    'horizon.framework.conf.resource-type-registry.service'
  ];

  function run(accountResCode, containerResCode, objectResCode, registryService) {
    registryService.getResourceType(accountResCode)
      .setNames('Swift Account', 'Swift Accounts',
                ngettext('Swift Account', 'Swift Accounts', 1));
    registryService.getResourceType(containerResCode)
      .setNames('Swift Container', 'Swift Containers',
                ngettext('Swift Container', 'Swift Containers', 1));

    var objectResourceType = registryService.getResourceType(objectResCode);
    objectResourceType.setNames('Object', 'Objects',
                                ngettext('Object', 'Objects', 1))
      .setProperty('name', {label: gettext('Name')})
      .setProperty('size', { label: gettext('Size')});

    objectResourceType.tableColumns.append({
      id: 'name', priority: 1, sortDefault: true,
      template: '<a ng-if="item.is_subdir" ng-href="{$ table.objectURL(item) $}">' +
        '{$ item.name $}</a><span ng-if="item.is_object">{$ item.name $}</span>'
    })
    .append({
      id: 'bytes', priority: 1, title: gettext('Size'),
      template: '<span ng-if="item.is_object">{$item.bytes | bytes$}</span>' +
        '<span ng-if="item.is_subdir" translate>Folder</span>'
    });

    objectResourceType.filterFacets.append({
      label: gettext('Name'),
      name: 'name',
      singleton: true
    });
  }
})();
