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
   * @ngname horizon.app.core.keypairs
   *
   * @description
   * Provides all of the services and widgets required
   * to support and display keypairs related content.
   */
  angular
    .module('horizon.app.core.keypairs', [
      'ngRoute',
      'horizon.app.core.keypairs.actions',
      'horizon.app.core.keypairs.details'
    ])
    .constant('horizon.app.core.keypairs.resourceType', 'OS::Nova::Keypair')
    .run(run)
    .config(config);

  run.$inject = [
    'horizon.framework.conf.resource-type-registry.service',
    'horizon.app.core.openstack-service-api.nova',
    'horizon.app.core.keypairs.basePath',
    'horizon.app.core.keypairs.resourceType',
    'horizon.app.core.keypairs.service'
  ];

  function run(registry, nova, basePath, resourceType, keypairsService) {
    registry.getResourceType(resourceType)
      .setNames('Key Pair', 'Key Pairs', ngettext('Key Pair', 'Key Pairs', 1))
      // for detail summary view on table row.
      .setSummaryTemplateUrl(basePath + 'details/drawer.html')
      .setDefaultIndexUrl('/project/key_pairs/')
      .setProperties(keypairProperties())
      .setListFunction(keypairsService.getKeypairsPromise)
      .tableColumns
      .append({
        id: 'name',
        priority: 1,
        sortDefault: true,
        classes: "word-wrap",
        urlFunction: keypairsService.urlFunction
      })
      .append({
        id: 'type',
        priority: 2
      })
      .append({
        id: 'fingerprint',
        priority: 3
      });

    // for magic-search
    registry.getResourceType(resourceType).filterFacets
      .append({
        'label': gettext('Name'),
        'name': 'name',
        'singleton': true
      });
  }

  function keypairProperties() {
    return {
      'id': {},
      'keypair_id': {label: gettext('ID'), filters: ['noValue'] },
      'name': {label: gettext('Name'), filters: ['noName'] },
      'type': {label: gettext('Type'), filters: ['noValue']},
      'fingerprint': {label: gettext('Fingerprint'), filters: ['noValue'] },
      'created_at': {label: gettext('Created'), filters: ['mediumDate'] },
      'user_id': {label: gettext('User ID'), filters: ['noValue'] },
      'public_key': {label: gettext('Public Key'), filters: ['noValue'] }
    };
  }

  config.$inject = [
    '$provide',
    '$windowProvider',
    '$routeProvider',
    'horizon.app.core.detailRoute'
  ];

  /**
   * @name config
   * @param {Object} $provide
   * @param {Object} $windowProvider
   * @param {Object} $routeProvider
   * @param {Object} detailRoute
   * @description Routes used by this module.
   * @returns {undefined} Returns nothing
   */
  function config($provide, $windowProvider, $routeProvider, detailRoute) {
    var path = $windowProvider.$get().STATIC_URL + 'app/core/keypairs/';
    $provide.constant('horizon.app.core.keypairs.basePath', path);
    $routeProvider.when('/project/key_pairs', {
      templateUrl: path + 'panel.html'
    })
    .when('/project/key_pairs/:id', {
      redirectTo: goToAngularDetails
    });

    function goToAngularDetails(params) {
      return detailRoute + 'OS::Nova::Keypair/' + params.id;
    }
  }
})();
