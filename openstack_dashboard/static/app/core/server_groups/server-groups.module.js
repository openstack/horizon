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
   * @ngdoc overview
   * @ngname horizon.app.core.server_groups
   *
   * @description
   * Provides all of the services and widgets required
   * to support and display server groups related content.
   */
  angular
    .module('horizon.app.core.server_groups', [
      'horizon.framework.conf',
      'horizon.app.core',
      'horizon.app.core.server_groups.actions',
      'horizon.app.core.server_groups.details'
    ])
    .constant('horizon.app.core.server_groups.resourceType', 'OS::Nova::ServerGroup')
    .run(run)
    .config(config);

  run.$inject = [
    'horizon.app.core.server_groups.resourceType',
    'horizon.app.core.server_groups.service',
    'horizon.framework.conf.resource-type-registry.service'
  ];

  function run(serverGroupResourceType,
               serverGroupsService,
               registry) {
    registry.getResourceType(serverGroupResourceType)
      .setNames('Server Group', 'Server Groups',
                ngettext('Server Group', 'Server Groups', 1))
      .setProperties(serverGroupProperties())
      .setListFunction(serverGroupsService.getServerGroupsPromise)
      .tableColumns
      .append({
        id: 'name',
        priority: 1,
        sortDefault: true,
        classes: "word-wrap",
        urlFunction: serverGroupsService.getDetailsPath
      })
      // The name is not unique, so we need to show the ID to
      // distinguish.
      .append({
        id: 'id',
        priority: 1
      })
      .append({
        id: 'policy',
        priority: 1
      });

    registry.getResourceType(serverGroupResourceType).filterFacets
      .append({
        label: gettext('Name'),
        name: 'name',
        singleton: true
      })
      .append({
        label: gettext('ID'),
        name: 'id',
        singleton: true
      })
      .append({
        label: gettext('Policy'),
        name: 'policy',
        singleton: true
      });
  }

  /**
   * @name serverGroupProperties
   * @description resource properties for server group module
   */
  function serverGroupProperties() {
    return {
      name: gettext('Name'),
      id: gettext('ID'),
      policy: gettext('Policy'),
      project_id: gettext('Project ID'),
      user_id: gettext('User ID')
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
   * @param {String} detailRoute
   * @description Routes used by this module.
   * @returns {undefined} Returns nothing
   */
  function config($provide, $windowProvider, $routeProvider, detailRoute) {
    var path = $windowProvider.$get().STATIC_URL + 'app/core/server_groups/';
    $provide.constant('horizon.app.core.server_groups.basePath', path);

    $routeProvider.when('/project/server_groups', {
      templateUrl: path + 'panel.html'
    });

    $routeProvider.when('/project/server_groups/:id', {
      redirectTo: goToAngularDetails
    });

    function goToAngularDetails(params) {
      return detailRoute + 'OS::Nova::ServerGroup/' + params.id;
    }
  }

})();
