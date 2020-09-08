/*
 * Copyright 2017 Ericsson
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
   * @ngname horizon.app.core.trunks
   *
   * @description
   * Provides all of the services and widgets required
   * to support and display trunks related content.
   */
  angular
    .module('horizon.app.core.trunks', [
      'ngRoute',
      'horizon.framework.conf',
      'horizon.app.core.trunks.actions',
      'horizon.app.core.trunks.details',
      'horizon.app.core'
    ])
    .constant('horizon.app.core.trunks.resourceType', 'OS::Neutron::Trunk')
    .constant('horizon.app.core.trunks.portConstants', portConstants())
    .run(run)
    .config(config);

  run.$inject = [
    'horizon.framework.conf.resource-type-registry.service',
    'horizon.framework.util.i18n.gettext',
    'horizon.app.core.trunks.basePath',
    'horizon.app.core.trunks.service',
    'horizon.app.core.trunks.resourceType'
  ];

  function run(registry,
               gettext,
               basePath,
               trunksService,
               trunkResourceType) {
    registry.getResourceType(trunkResourceType)
      .setNames('Trunk', 'Trunks', ngettext('Trunk', 'Trunks', 1))
      .setSummaryTemplateUrl(basePath + 'summary.html')
      .setDefaultIndexUrl('/project/trunks/')
      .setProperties(trunkProperties())
      .setListFunction(trunksService.getTrunksPromise)
      .tableColumns
      .append({
        id: 'name_or_id',
        priority: 1,
        sortDefault: true,
        classes: "word-wrap",
        urlFunction: trunksService.getDetailsPath
      })
      .append({
        id: 'port_id',
        priority: 1,
        urlFunction: trunksService.getPortDetailsPath
      })
      .append({
        id: 'subport_count',
        priority: 1
      })
      .append({
        id: 'admin_state',
        priority: 1
      })
      .append({
        id: 'status',
        priority: 1
      });

    /**
     * Filtering - client-side MagicSearch
     * all facets for trunks table
     */
    registry.getResourceType(trunkResourceType).filterFacets
      .append({
        label: gettext('Name'),
        name: 'name',
        singleton: true
      })
      .append({
        label: gettext('Parent Port'),
        name: 'port_id',
        singleton: true
      })
      .append({
        label: gettext('Status'),
        name: 'status',
        singleton: true,
        options: [
          {label: gettext('Active'), key: 'ACTIVE'},
          {label: gettext('Down'), key: 'DOWN'},
          {label: gettext('Build'), key: 'BUILD'},
          {label: gettext('Degraded'), key: 'DEGRADED'},
          {label: gettext('Error'), key: 'ERROR'}
        ]
      })
      .append({
        label: gettext('Admin State'),
        name: 'admin_state_up',
        singleton: true,
        options: [
          {label: gettext('Up'), key: 'true'},
          {label: gettext('Down'), key: 'false'}
        ]
      });
  }

  /**
   * @name trunkProperties
   * @description resource properties for trunk module
   */
  function trunkProperties() {
    return {
      admin_state: gettext('Admin State'),
      created_at: gettext('Created at'),
      description: gettext('Description'),
      id: gettext('ID'),
      name: gettext('Name'),
      name_or_id: gettext('Name/ID'),
      port_id: gettext('Parent Port'),
      project_id: gettext('Project ID'),
      status: gettext('Status'),
      subport_count: gettext('Subport Count'),
      updated_at: gettext('Updated at')
    };
  }

  function portConstants() {
    return {
      statuses: {
        'ACTIVE': gettext('Active'),
        'DOWN': gettext('Down')
      },
      adminStates: {
        'UP': gettext('Up'),
        'DOWN': gettext('Down')
      },
      vnicTypes: {
        'normal': gettext('Normal'),
        'direct': gettext('Direct'),
        'direct-physical': gettext('Direct Physical'),
        'macvtap': gettext('MacVTap'),
        'baremetal': gettext('Bare Metal')
      }
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
    var path = $windowProvider.$get().STATIC_URL + 'app/core/trunks/';
    $provide.constant('horizon.app.core.trunks.basePath', path);

    $routeProvider.when('/project/trunks', {
      templateUrl: path + 'panel.html'
    });

    $routeProvider.when('/project/trunks/:id', {
      redirectTo: goToAngularDetails
    });

    $routeProvider.when('/admin/trunks', {
      templateUrl: path + 'panel.html'
    });

    $routeProvider.when('/admin/trunk/:id/detail', {
      redirectTo: goToAngularDetails
    });

    function goToAngularDetails(params) {
      return detailRoute + 'OS::Neutron::Trunk/' + params.id;
    }
  }

})();
