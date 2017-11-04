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

  angular.module('horizon.app.core.server_groups')
    .factory('horizon.app.core.server_groups.service', serverGroupsService);

  serverGroupsService.$inject = [
    'horizon.app.core.openstack-service-api.nova'
  ];

  /*
   * @ngdoc factory
   * @name horizon.app.core.server_groups.service
   *
   * @description
   * This service provides functions that are used through the Server Groups
   * features. These are primarily used in the module registrations
   * but do not need to be restricted to such use.  Each exposed function
   * is documented below.
   */
  function serverGroupsService(nova) {
    return {
      getServerGroupsPromise: getServerGroupsPromise
    };

    /*
     * @ngdoc function
     * @name getServerGroupPolicies
     * @description
     * Returns a list for the server group policies.
     */
    function getServerGroupPolicies() {
      return nova.isFeatureSupported('servergroup_soft_policies')
          .then(isSoftPoliciesSupported);

      function isSoftPoliciesSupported(response) {
        var policies = {
          'affinity': gettext('Affinity'),
          'anti-affinity': gettext('Anti Affinity')
        };
        if (response.data) {
          policies['soft-anti-affinity'] = gettext('Soft Anti Affinity');
          policies['soft-affinity'] = gettext('Soft Affinity');
        }
        return policies;
      }
    }

    /*
     * @ngdoc function
     * @name getServerGroupsPromise
     * @description
     * Rreturns a promise for the matching server groups.
     * This is used in displaying lists of Server Groups.
     */
    function getServerGroupsPromise() {
      return nova.getServerGroups().then(modifyResponse);

      function modifyResponse(response) {
        return getServerGroupPolicies().then(modifyItems);

        function modifyItems(policies) {
          response.data.items.map(function (item) {
            // When creating a server group, the back-end limit
            // server group can only have one policy.
            item.policy = policies[item.policies[0]];
          });
          return {data: {items: response.data.items}};
        }
      }
    }
  }

})();
