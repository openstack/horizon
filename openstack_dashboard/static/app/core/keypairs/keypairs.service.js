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

  angular.module('horizon.app.core.keypairs')
    .factory('horizon.app.core.keypairs.service', keypairsService);

  keypairsService.$inject = [
    'horizon.app.core.detailRoute',
    'horizon.app.core.openstack-service-api.nova'
  ];

  /*
  * @ngdoc factory
  * @name horizon.app.core.keypairs.service
  *
  * @description
  * This service provides functions that are used through the key pair
  * features.  These are primarily used in the module registrations
  * but do not need to be restricted to such use.  Each exposed function
  * is documented below.
  */
  function keypairsService(detailRoute, nova) {
    return {
      getKeypairsPromise: getKeypairsPromise,
      getKeypairPromise: getKeypairPromise,
      urlFunction: urlFunction
    };

     /*
      * @ngdoc function
      * @name getKeypairsPromise
      * @description
      * Given filter/query parameters, returns a promise for the matching
      * key pairs.  This is used in displaying lists of key pairs.  In this
      * case, we need to modify the API's response by adding a composite value
      * called 'trackBy' to assist the display mechanism when updating rows.
      */
    function getKeypairsPromise(params) {
      return nova.getKeypairs(params).then(modifyResponse);

      function modifyResponse(response) {
        return {data: {items: response.data.items.map(modifyItem)}};

        function modifyItem(item) {
          item = item.keypair;
          item.id = item.name;
          item.trackBy = item.name + item.fingerprint;
          return item;
        }
      }
    }

    /*
     * @ngdoc function
     * @name getKeypairPromise
     * @description
     * Given a name, returns a promise for the keypair data.
     */
    function getKeypairPromise(name) {
      return nova.getKeypair(name);
    }

    function urlFunction(item) {
      return detailRoute + 'OS::Nova::Keypair/' + item.name;
    }
  }
})();
