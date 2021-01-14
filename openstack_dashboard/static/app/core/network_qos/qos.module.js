/*
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *    http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

(function() {
  'use strict';

  /**
   * @ngdoc horizon.dashboard.project.network_qos
   * @ngModule
   *
   * @description
   * Provides all of the services and widgets required
   * to support and display the QoS panel.
   */
  angular
    .module('horizon.app.core.network_qos', [
      'ngRoute',
      'horizon.framework.conf',
      'horizon.app.core.network_qos.actions',
      'horizon.app.core.network_qos.details',
      'horizon.app.core'
    ])
    .constant('horizon.app.core.network_qos.resourceType', 'OS::Neutron::QoSPolicy')
    .run(run)
    .config(config);

  run.$inject = [
    'horizon.framework.conf.resource-type-registry.service',
    'horizon.framework.util.i18n.gettext',
    'horizon.app.core.network_qos.basePath',
    'horizon.app.core.network_qos.service',
    'horizon.app.core.network_qos.resourceType'
  ];

  function run(registry,
               gettext,
               basePath,
               qosService,
               qosResourceType) {
    registry.getResourceType(qosResourceType)
      .setNames('QoS Policy', 'QoS Policies',
                ngettext('QoS Policy', 'QoS Policies', 1))
      .setSummaryTemplateUrl(basePath + 'details/drawer.html')
      .setDefaultIndexUrl('/project/network_qos/')
      .setProperties(qosProperties(qosService))
      .setListFunction(qosService.getPoliciesPromise)
      .tableColumns
      .append({
        id: 'name',
        priority: 1,
        sortDefault: true,
        urlFunction: qosService.getDetailsPath
      })
      .append({
        id: 'description',
        priority: 1
      })
      .append({
        id: 'shared',
        priority: 1
      });

    registry.getResourceType(qosResourceType).filterFacets
      .append({
        label: gettext('Policy Name'),
        name: 'name',
        singleton: true,
        persistent: true
      })
      .append({
        label: gettext('Description'),
        name: 'description',
        singleton: true
      })
      .append({
        label: gettext('Shared'),
        name: 'shared',
        singleton: true,
        options: [
          {label: gettext('Yes'), key: 'true'},
          {label: gettext('No'), key: 'false'}
        ]
      });
  }

  /**
   * @name qosProperties
   * @description resource properties for QoS module
   */
  function qosProperties() {
    return {
      'name': {label: gettext('Policy Name'), filters: ['noName'] },
      'id': {label: gettext('Policy ID'), filters: ['noValue'] },
      'description': {label: gettext('Description'), filters: ['noName'] },
      'shared': {label: gettext('Shared'), filters: ['yesno'] },
      'tenant_id': {label: gettext('Tenant ID'), filters: ['noValue'] },
      'project_id': {label: gettext('Project ID'), filters: ['noValue'] },
      'created_at': {label: gettext('Created At'), filters: ['simpleDate'] },
      'updated_at': {label: gettext('Updated At'), filters: ['simpleDate'] },
      'rules': {label: gettext('Rules'), filters: ['noValue'] },
      'revision_number': {label: gettext('Revision Number'), filters: ['noValue'] }
    };
  }

  config.$inject = [
    '$provide',
    '$windowProvider',
    '$routeProvider',
    'horizon.app.core.detailRoute'
  ];

  /**
   * @name horizon.dashboard.project.network_qos.basePath
   * @param {Object} $provide
   * @param {Object} $windowProvider
   * @param {Object} $routeProvider
   * @param {Object} detailRoute
   * @description Base path for the QoS code
   */
  function config($provide, $windowProvider, $routeProvider, detailRoute) {
    var path = $windowProvider.$get().STATIC_URL + 'app/core/network_qos/';
    $provide.constant('horizon.app.core.network_qos.basePath', path);

    $routeProvider
    .when('/project/network_qos', {
      templateUrl: path + 'panel.html'
    })
    .when('/project/network_qos/:id', {
      redirectTo: goToAngularDetails
    });

    function goToAngularDetails(params) {
      return detailRoute + 'OS::Neutron::QoSPolicy/' + params.id;
    }
  }

})();
