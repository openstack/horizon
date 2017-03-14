/*
 * Licensed under the Apache License, Version 2.0 (the 'License');
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *    http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an 'AS IS' BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */
(function() {
  "use strict";

  angular
    .module('horizon.app.core.network_qos')
    .controller('NetworkQoSOverviewController', NetworkQoSOverviewController);

  NetworkQoSOverviewController.$inject = [
    'horizon.app.core.network_qos.resourceType',
    'horizon.framework.conf.resource-type-registry.service',
    'horizon.app.core.openstack-service-api.userSession',
    '$scope'
  ];

  function NetworkQoSOverviewController(
    qosResourceTypeCode,
    registry,
    userSession,
    $scope
  ) {
    var ctrl = this;

    ctrl.resourceType = registry.getResourceType(qosResourceTypeCode);
    ctrl.tableConfig = {
      selectAll: false,
      expand: false,
      trackId: 'id',
      /*
       * getTableColumns here won't work as that will give back the
       * columns for the policy, but here we need columns only for the
       * policy rules, which is a (list of) dictionary(ies) in the
       * policy dictionary.
       */
      columns: [
        {id: 'id', title: gettext('Rule ID'), priority: 1, sortDefault: true},
        {id: 'type', title: gettext('Type'), priority: 1},
        {id: 'direction', title: gettext('Direction'), priority: 1},
        {id: 'max_kbps', title: gettext('Max Kbps'), priority: 1},
        {id: 'max_burst_kbps', title: gettext('Max Burst Kbits'), priority: 1},
        {id: 'min_kbps', title: gettext('Min Kbps'), priority: 1},
        {id: 'dscp_mark', title: gettext('DSCP Mark'), priority: 1}
      ]
    };

    $scope.context.loadPromise.then(onGetPolicy);

    function onGetPolicy(response) {
      ctrl.policy = response.data;

      userSession.get().then(setProject);

      function setProject(session) {
        ctrl.projectId = session.project_id;
      }
    }
  }

})();
