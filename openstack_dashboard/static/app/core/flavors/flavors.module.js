/**
 * (c) Copyright 2015 Hewlett-Packard Development Company, L.P.
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
   * @ngname horizon.app.core.flavors
   *
   * @description
   * Provides all of the services and widgets required
   * to support and display flavors related content.
   */
  angular
    .module('horizon.app.core.flavors', [
      'ngRoute',
      'horizon.framework.conf',
      'horizon.app.core',
      'horizon.app.core.flavors.actions'
    ])
    .constant('horizon.app.core.flavors.resourceType', 'OS::Nova::Flavor')
    .run(run)
    .config(config);

  run.$inject = [
    'horizon.framework.conf.resource-type-registry.service',
    'horizon.framework.util.i18n.gettext',
    'horizon.app.core.flavors.basePath',
    'horizon.app.core.flavors.service',
    'horizon.app.core.flavors.resourceType'
  ];

  function run(registry, gettext, basePath, flavorsService, flavorResourceType) {
    registry.getResourceType(flavorResourceType)
      .setNames('Flavor', 'Flavors', ngettext('Flavor', 'Flavors', 1))
      .setSummaryTemplateUrl(basePath + 'summary.html')
      .setProperties(flavorProperties())
      .setListFunction(flavorsService.getFlavorsPromise)
      .tableColumns
      .append({
        id: 'name',
        priority: 1
      })
      .append({
        id: 'vcpus',
        priority: 2
      })
      .append({
        id: 'ram',
        priority: 1,
        sortDefault: true
      })
      .append({
        id: 'disk',
        priority: 2
      })
      .append({
        id: 'id',
        priority: 1
      })
      .append({
        id: 'os-flavor-access:is_public',
        priority: 2
      });

    /**
     * Filtering - client-side MagicSearch
     * all facets for flavor table
     */
    registry.getResourceType(flavorResourceType).filterFacets
      .append({
        label: gettext('Name'),
        name: 'name',
        singleton: true
      })
      .append({
        label: gettext('VCPUs'),
        name: 'vcpus',
        singleton: true
      })
      .append({
        label: gettext('RAM'),
        name: 'ram',
        singleton: true
      })
      .append({
        label: gettext('Root Disk'),
        name: 'disk',
        singleton: true
      })
      .append({
        label: gettext('Public'),
        name: 'os-flavor-access:is_public',
        singleton: true,
        options: [
          {label: gettext('Yes'), key: 'true'},
          {label: gettext('No'), key: 'false'}
        ]
      });

      /**
     * @name roleProperties
     * @description resource properties for flavor module
     */
    function flavorProperties() {
      return {
        name: gettext('Flavor Name'),
        vcpus: gettext('VCPUs'),
        ram: {label: gettext('RAM'), filters: ['mb']},
        disk: {label: gettext('Root Disk'), filters: ['gb']},
        'OS-FLV-EXT-DATA:ephemeral': {label: gettext('Ephemeral Disk'), filters: ['gb']},
        swap: {label: gettext('Swap Disk'), filters: ['gb']},
        rxtx_factor: gettext('RX/TX Factor'),
        id: gettext('ID'),
        'os-flavor-access:is_public': {label: gettext('Public'), filters: ['yesno']},
        metadata: gettext('Metadata')
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
    var path = $windowProvider.$get().STATIC_URL + 'app/core/flavors/';
    $provide.constant('horizon.app.core.flavors.basePath', path);

    $routeProvider.when('/admin/flavors', {
      templateUrl: path + 'panel.html'
    });
  }

})();
