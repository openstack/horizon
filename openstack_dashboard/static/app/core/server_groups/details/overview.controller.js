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
  "use strict";

  angular
    .module('horizon.app.core.server_groups')
    .controller('ServerGroupOverviewController', ServerGroupOverviewController);

  ServerGroupOverviewController.$inject = [
    '$scope',
    'horizon.app.core.openstack-service-api.nova',
    'horizon.app.core.openstack-service-api.userSession',
    'horizon.app.core.server_groups.resourceType',
    'horizon.app.core.server_groups.service',
    'horizon.framework.conf.resource-type-registry.service'
  ];

  function ServerGroupOverviewController(
    $scope,
    nova,
    userSession,
    serverGroupResourceTypeCode,
    serverGroupsService,
    registry
  ) {
    var ctrl = this;

    nova.isFeatureSupported(
      'servergroup_user_info').then(onGetServerGroupProperties);

    function onGetServerGroupProperties(response) {
      var properties = ['id', 'name', 'policy'];
      if (response.data) {
        properties.splice(2, 0, 'project_id', 'user_id');
      }
      ctrl.properties = properties;
    }

    ctrl.resourceType = registry.getResourceType(serverGroupResourceTypeCode);
    ctrl.tableConfig = {
      selectAll: false,
      expand: false,
      trackId: 'id',
      columns: [
        {
          id: 'name',
          title: gettext('Instance Name'),
          priority: 1,
          sortDefault: true,
          urlFunction: serverGroupsService.getInstanceDetailsPath
        },
        {
          id: 'id',
          title: gettext('Instance ID'),
          priority: 1
        }
      ]
    };

    $scope.context.loadPromise.then(onGetServerGroup);

    function onGetServerGroup(servergroup) {
      ctrl.servergroup = servergroup.data;
      if (ctrl.servergroup.members.length) {
        // The server group members only contains the instance id,
        // does not contain other information of the instance, we
        // need to get the list of instances and then get the specified
        // instance from the list based on id.
        nova.getServers().then(function getServer(servers) {
          var members = [];
          ctrl.servergroup.members.forEach(function(member) {
            for (var i = 0; i < servers.data.items.length; i++) {
              var server = servers.data.items[i];
              if (member === server.id) {
                members.push(server);
                break;
              }
            }
          });
          ctrl.members = members;
        });
      } else {
        ctrl.members = [];
      }

      userSession.get().then(setProject);

      function setProject(session) {
        ctrl.projectId = session.project_id;
      }
    }
  }

})();
