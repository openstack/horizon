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

  angular.module('horizon.app.core.network_qos')
    .factory('horizon.app.core.network_qos.service', qosService);

  qosService.$inject = [
    'horizon.app.core.openstack-service-api.neutron',
    'horizon.app.core.openstack-service-api.userSession',
    'horizon.app.core.detailRoute'
  ];

  /*
  * @ngdoc factory
  * @name horizon.app.core.network_qos.service
  *
  * @description
  * This service provides functions that are used through the QoS
  * features.  These are primarily used in the module registrations
  * but do not need to be restricted to such use.  Each exposed function
  * is documented below.
  */
  function qosService(neutron,
                      userSession,
                      detailRoute) {
    var version;

    return {
      getDetailsPath: getDetailsPath,
      getPoliciesPromise: getPoliciesPromise,
      getPolicyPromise: getPolicyPromise
    };

    /*
     * @ngdoc function
     * @name getDetailsPath
     * @param item {Object} - The QoS Policy object
     * @description
     * Given an QoS Policy object, returns the relative path to the details
     * view.
     */
    function getDetailsPath(item) {
      return detailRoute + 'OS::Neutron::QoSPolicy/' + item.id;
    }

     /*
      * @ngdoc function
      * @name getPoliciesPromise
      * @description
      * Given filter/query parameters, returns a promise for the matching
      * policies.  This is used in displaying lists of policies.  In this case,
      * we need to modify the API's response by adding a composite value called
      * 'trackBy' to assist the display mechanism when updating rows.
      */
    function getPoliciesPromise(params) {
      return userSession.get().then(getQoSPolicies);

      function getQoSPolicies() {
        return neutron.getQoSPolicies(params).then(modifyResponse);
      }

      function modifyResponse(response) {
        return {data: {items: response.data.items.map(modifyQos)}};

        function modifyQos(policy) {
          policy.trackBy = policy.id;
          policy.apiVersion = version;
          policy.name = policy.name || policy.id;
          return policy;
        }
      }
    }

    /*
    * @ngdoc function
    * @name getPolicyPromise
    * @description
    * Given an id, returns a promise for the policy data.
    */
    function getPolicyPromise(identifier) {
      return neutron.getQosPolicy(identifier);
    }

  }

})();
